from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import randbelow
from typing import Optional

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import PasswordResetTokenModel


class DatabaseResetTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: int) -> str:
        token = f"{randbelow(1_000_000):06d}"
        reset_token = PasswordResetTokenModel(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            used=False,
        )
        self._session.add(reset_token)
        await self._session.commit()
        return token

    async def consume(self, *, token: str) -> Optional[int]:
        stmt = (
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.token == token,
                PasswordResetTokenModel.used.is_(False),
                PasswordResetTokenModel.expires_at > datetime.now(timezone.utc),
            )
            .values(used=True)
            .returning(PasswordResetTokenModel.user_id)
        )
        result = await self._session.execute(stmt)
        user_id = result.scalar_one_or_none()
        if user_id is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return int(user_id)
