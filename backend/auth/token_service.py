from __future__ import annotations

from datetime import datetime, timezone
from typing import Union

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt_service import JWTError, JWTService
from backend.auth.models import AuthRefreshSessionModel
from backend.auth.schemas import AuthTokenRead
from backend.user.migrations import is_admin_phone
from backend.user.models import UserModel
from backend.user.schemas import UserRead


class AuthTokenError(Exception):
    pass


class AuthTokenService:
    def __init__(self) -> None:
        self.jwt_service = JWTService()

    async def issue_token_pair(self, *, session: AsyncSession, user: Union[UserRead, UserModel]) -> AuthTokenRead:
        user_read = UserRead.model_validate(user)
        env_admin = is_admin_phone(user_read.phone)
        if user_read.is_admin != env_admin:
            if isinstance(user, UserModel):
                user.is_admin = env_admin
                await session.flush()
                user_read = UserRead.model_validate(user)
            else:
                user_read = user_read.model_copy(update={"is_admin": env_admin})

        access_token, access_expires_in = self.jwt_service.create_access_token(
            user_id=user_read.id,
            is_admin=user_read.is_admin,
        )
        refresh_token, jti, refresh_exp, refresh_expires_in = self.jwt_service.create_refresh_token(
            user_id=user_read.id,
        )
        session.add(
            AuthRefreshSessionModel(
                user_id=user_read.id,
                jti=jti,
                expires_at=refresh_exp,
                revoked=False,
            )
        )
        await session.commit()
        return AuthTokenRead(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=access_expires_in,
            refresh_expires_in=refresh_expires_in,
            user=user_read,
        )

    async def refresh_token_pair(self, *, session: AsyncSession, refresh_token: str) -> AuthTokenRead:
        try:
            payload = self.jwt_service.decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise AuthTokenError("Invalid refresh token.") from exc

        user_id = int(payload["user_id"])
        jti = str(payload["jti"])
        refresh_session = await session.scalar(
            select(AuthRefreshSessionModel).where(
                AuthRefreshSessionModel.user_id == user_id,
                AuthRefreshSessionModel.jti == jti,
                AuthRefreshSessionModel.revoked.is_(False),
            )
        )
        if refresh_session is None:
            raise AuthTokenError("Invalid refresh token.")

        now = datetime.now(timezone.utc)
        expires_at = refresh_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= now:
            refresh_session.revoked = True
            await session.commit()
            raise AuthTokenError("Refresh token expired.")

        user = await session.scalar(select(UserModel).where(UserModel.id == user_id))
        if user is None:
            raise AuthTokenError("User not found.")

        refresh_session.revoked = True
        return await self.issue_token_pair(session=session, user=user)

    async def revoke_refresh_token(self, *, session: AsyncSession, refresh_token: str) -> None:
        try:
            payload = self.jwt_service.decode_refresh_token(refresh_token)
        except JWTError as exc:
            raise AuthTokenError("Invalid refresh token.") from exc

        stmt = (
            update(AuthRefreshSessionModel)
            .where(
                AuthRefreshSessionModel.user_id == int(payload["user_id"]),
                AuthRefreshSessionModel.jti == str(payload["jti"]),
                AuthRefreshSessionModel.revoked.is_(False),
            )
            .values(revoked=True)
        )
        await session.execute(stmt)
        await session.commit()
