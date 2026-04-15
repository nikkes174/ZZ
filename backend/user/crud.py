from __future__ import annotations

from typing import Optional, Protocol

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.user.models import UserModel


class UserRepository(Protocol):
    async def get_by_id(self, user_id: int) -> Optional[UserModel]: ...
    async def get_by_phone(self, phone: str) -> Optional[UserModel]: ...
    async def get_by_session_token(self, session_token: str) -> Optional[UserModel]: ...
    async def create_user(
        self,
        *,
        phone: str,
        password_hash: str,
        full_name: Optional[str],
        session_token: str,
        is_admin: bool,
    ) -> UserModel: ...
    async def activate_existing_user(
        self,
        *,
        user_id: int,
        password_hash: str,
        full_name: Optional[str],
        session_token: str,
        is_admin: bool,
    ) -> UserModel: ...
    async def update_session_token(self, *, user_id: int, session_token: str, is_admin: bool) -> UserModel: ...
    async def clear_session_token(self, *, user_id: int) -> Optional[UserModel]: ...
    async def update_admin_status(self, *, user_id: int, is_admin: bool) -> UserModel: ...
    async def update_phone(self, *, user_id: int, phone: str, is_admin: bool) -> UserModel: ...
    async def add_bonus(self, *, user_id: int, bonus_delta: int) -> Optional[UserModel]: ...
    async def spend_bonus(self, *, user_id: int, bonus_amount: int) -> Optional[UserModel]: ...


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        return await self._session.scalar(stmt)

    async def get_by_phone(self, phone: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.phone == phone)
        return await self._session.scalar(stmt)

    async def get_by_session_token(self, session_token: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.session_token == session_token)
        return await self._session.scalar(stmt)

    async def create_user(
        self,
        *,
        phone: str,
        password_hash: str,
        full_name: Optional[str],
        session_token: str,
        is_admin: bool,
    ) -> UserModel:
        user = UserModel(
            phone=phone,
            full_name=full_name,
            password_hash=password_hash,
            is_admin=is_admin,
            is_verified=True,
            session_token=session_token,
            verification_code=None,
            verification_expires_at=None,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def activate_existing_user(
        self,
        *,
        user_id: int,
        password_hash: str,
        full_name: Optional[str],
        session_token: str,
        is_admin: bool,
    ) -> UserModel:
        values: dict[str, object] = {
            "password_hash": password_hash,
            "is_admin": is_admin,
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

    async def update_session_token(self, *, user_id: int, session_token: str, is_admin: bool) -> UserModel:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                is_admin=is_admin,
                is_verified=True,
                session_token=session_token,
            )
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        await self._session.commit()
        return user

    async def clear_session_token(self, *, user_id: int) -> Optional[UserModel]:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(session_token=None)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return user

    async def update_admin_status(self, *, user_id: int, is_admin: bool) -> UserModel:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(is_admin=is_admin)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one()
        await self._session.commit()
        return user

    async def update_phone(self, *, user_id: int, phone: str, is_admin: bool) -> UserModel:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(phone=phone, is_admin=is_admin)
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

    async def spend_bonus(self, *, user_id: int, bonus_amount: int) -> Optional[UserModel]:
        stmt = (
            update(UserModel)
            .where(
                UserModel.id == user_id,
                UserModel.bonus_balance >= bonus_amount,
            )
            .values(bonus_balance=UserModel.bonus_balance - bonus_amount)
            .returning(UserModel)
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return user
