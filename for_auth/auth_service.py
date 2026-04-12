import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import ADMIN_TG_IDS, BOT_TOKEN
from backend.exceptions import (
    InfrastructureError,
    InvalidRefreshTokenError,
    InvalidTelegramInitDataError,
)
from backend.user.models import User

from .jwt_service import JWTService
from .models import AuthRefreshSession
from .telegram_auth import validate_telegram_init_data

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self):
        self.jwt_service = JWTService()

    async def auth_telegram_user(
        self,
        db: AsyncSession,
        init_data: str,
    ) -> User:
        try:
            data = validate_telegram_init_data(init_data, BOT_TOKEN)
        except InvalidTelegramInitDataError:
            raise
        except Exception as exc:
            logger.exception("Unexpected Telegram init-data validation failure")
            raise InvalidTelegramInitDataError() from exc

        try:
            user_data_raw = data.get("user")
            user_data = json.loads(user_data_raw) if user_data_raw else {}
            telegram_id = int(user_data["id"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Invalid Telegram user payload")
            raise InvalidTelegramInitDataError() from exc

        start_param = data.get("start_param")

        try:
            result = await db.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
        except OperationalError as exc:
            logger.exception("Database read failed during auth")
            raise InfrastructureError("Database read failed") from exc

        if user:
            expected_admin = telegram_id in ADMIN_TG_IDS
            if user.is_admin != expected_admin:
                user.is_admin = expected_admin
                await self._commit_with_retry(db, "syncing user role")
                await db.refresh(user)
            return user

        user = User(
            telegram_id=telegram_id,
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            username=user_data.get("username"),
            source=start_param or "telegram",
            platform="telegram",
            is_admin=telegram_id in ADMIN_TG_IDS,
        )

        try:
            db.add(user)
            await self._commit_with_retry(db, "creating user")
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            # Parallel auth requests can race on the unique telegram_id.
            result = await db.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            existing_user = result.scalar_one_or_none()
            if existing_user is None:
                logger.exception("User upsert conflict without persisted row")
                raise InfrastructureError("User upsert failed")
            return existing_user

    async def issue_token_pair(self, db: AsyncSession, user: User) -> dict:
        access_token, access_expires_in = self.jwt_service.create_access_token(
            tg_id=user.tg_id,
            is_admin=user.is_admin,
        )
        refresh_token, jti, refresh_exp, refresh_expires_in = self.jwt_service.create_refresh_token(
            tg_id=user.tg_id
        )

        session = AuthRefreshSession(
            tg_id=user.tg_id,
            jti=jti,
            expires_at=refresh_exp.replace(tzinfo=None),
            revoked=False,
        )
        db.add(session)
        await self._commit_with_retry(db, "issuing refresh session")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": access_expires_in,
            "refresh_expires_in": refresh_expires_in,
            "tg_id": user.tg_id,
            "user_id": user.tg_id,
            "is_admin": user.is_admin,
        }

    async def issue_dev_admin_token_pair(self, db: AsyncSession, tg_id: int) -> dict:
        result = await db.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=tg_id,
                first_name="Dev",
                last_name="Admin",
                username=f"dev_admin_{tg_id}",
                source="dev",
                platform="telegram",
                is_admin=True,
            )
            db.add(user)
            await self._commit_with_retry(db, "creating dev admin user")
            await db.refresh(user)
        elif not user.is_admin:
            user.is_admin = True
            await self._commit_with_retry(db, "promoting dev admin user")
            await db.refresh(user)

        return await self.issue_token_pair(db, user)

    async def issue_dev_user_token_pair(self, db: AsyncSession, tg_id: int) -> dict:
        result = await db.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=tg_id,
                first_name="Dev",
                last_name="User",
                username=f"dev_user_{tg_id}",
                source="dev",
                platform="telegram",
                is_admin=False,
            )
            db.add(user)
            await self._commit_with_retry(db, "creating dev user")
            await db.refresh(user)
        elif user.is_admin:
            user.is_admin = False
            await self._commit_with_retry(db, "demoting dev user")
            await db.refresh(user)

        return await self.issue_token_pair(db, user)

    async def refresh_token_pair(self, db: AsyncSession, refresh_token: str) -> dict:
        payload = self.jwt_service.decode_refresh_token(refresh_token)
        tg_id = int(payload["tg_id"])
        jti = str(payload["jti"])

        result = await db.execute(
            select(AuthRefreshSession).where(
                AuthRefreshSession.tg_id == tg_id,
                AuthRefreshSession.jti == jti,
                AuthRefreshSession.revoked.is_(False),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise InvalidRefreshTokenError()

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if session.expires_at <= now:
            session.revoked = True
            await self._commit_with_retry(db, "revoking expired refresh session")
            raise InvalidRefreshTokenError()

        result = await db.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            raise InvalidRefreshTokenError()

        session.revoked = True

        access_token, access_expires_in = self.jwt_service.create_access_token(
            tg_id=user.tg_id,
            is_admin=user.is_admin,
        )
        new_refresh_token, new_jti, new_refresh_exp, refresh_expires_in = self.jwt_service.create_refresh_token(
            tg_id=user.tg_id
        )

        new_session = AuthRefreshSession(
            tg_id=user.tg_id,
            jti=new_jti,
            expires_at=new_refresh_exp.replace(tzinfo=None),
            revoked=False,
        )
        db.add(new_session)
        await self._commit_with_retry(db, "rotating refresh session")

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": access_expires_in,
            "refresh_expires_in": refresh_expires_in,
            "tg_id": user.tg_id,
            "user_id": user.tg_id,
            "is_admin": user.is_admin,
        }

    async def revoke_refresh_token(self, db: AsyncSession, refresh_token: str) -> None:
        payload = self.jwt_service.decode_refresh_token(refresh_token)
        tg_id = int(payload["tg_id"])
        jti = str(payload["jti"])

        result = await db.execute(
            select(AuthRefreshSession).where(
                AuthRefreshSession.tg_id == tg_id,
                AuthRefreshSession.jti == jti,
                AuthRefreshSession.revoked.is_(False),
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise InvalidRefreshTokenError()

        session.revoked = True
        await self._commit_with_retry(db, "revoking refresh session")

    async def _commit_with_retry(self, db: AsyncSession, action: str) -> None:
        for attempt in range(1, 4):
            try:
                await db.commit()
                return
            except OperationalError as exc:
                await db.rollback()
                message = str(exc).lower()
                is_locked = "database is locked" in message or "database table is locked" in message
                if not is_locked or attempt == 3:
                    logger.exception("Database write failed while %s", action)
                    raise InfrastructureError("Database write failed") from exc
                logger.warning("SQLite locked while %s, retry attempt=%s", action, attempt)
                await asyncio.sleep(0.05 * attempt)
