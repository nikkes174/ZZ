from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.user.models import UserModel


class UserRepository(Protocol):
    async def get_by_phone(self, phone: str) -> Optional[UserModel]: ...
    async def get_by_session_token(self, session_token: str) -> Optional[UserModel]: ...
    async def create_or_update_code(
        self,
        *,
        phone: str,
        code: str,
        expires_at: datetime,
    ) -> UserModel: ...
    async def verify_user(
        self,
        *,
        user_id: int,
        full_name: str | None,
        session_token: str,
    ) -> UserModel: ...
    async def add_bonus(self, *, user_id: int, bonus_delta: int) -> Optional[UserModel]: ...


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_phone(self, phone: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.phone == phone)
        return await self._session.scalar(stmt)

    async def get_by_session_token(self, session_token: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.session_token == session_token)
        return await self._session.scalar(stmt)

    async def create_or_update_code(
        self,
        *,
        phone: str,
        code: str,
        expires_at: datetime,
    ) -> UserModel:
        user = await self.get_by_phone(phone)
        if user is None:
            user = UserModel(
                phone=phone,
                verification_code=code,
                verification_expires_at=expires_at,
            )
            self._session.add(user)
        else:
            user.verification_code = code
            user.verification_expires_at = expires_at

        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def verify_user(
        self,
        *,
        user_id: int,
        full_name: str | None,
        session_token: str,
    ) -> UserModel:
        values: dict[str, object] = {
            "is_verified": True,
            "session_token": session_token,
            "verification_code": None,
            "verification_expires_at": None,
        }
        if full_name:
            values["full_name"] = full_name

        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(**values)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        await self._session.commit()
        return user

    async def add_bonus(self, *, user_id: int, bonus_delta: int) -> Optional[UserModel]:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(bonus_balance=UserModel.bonus_balance + bonus_delta)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return user
