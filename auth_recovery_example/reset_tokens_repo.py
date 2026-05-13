import datetime as dt
import secrets
import uuid
from abc import ABC, abstractmethod

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.User.models import PasswordResetTokenModel


class ResetTokenRepository(ABC):
    @abstractmethod
    async def create(self, user_id): ...

    @abstractmethod
    async def consume(self, token: str) -> uuid.UUID | None: ...


class DatabaseResetTokenRepo(ResetTokenRepository):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
            minutes=10,
        )

        obj = PasswordResetTokenModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            used=False,
        )

        self.session.add(obj)
        await self.session.commit()
        return token

    async def consume(self, token: str) -> uuid.UUID | None:
        stmt = (
            update(PasswordResetTokenModel)
            .where(
                PasswordResetTokenModel.token == token,
                PasswordResetTokenModel.used.is_(False),
                PasswordResetTokenModel.expires_at
                > dt.datetime.now(dt.timezone.utc),
            )
            .values(used=True)
            .returning(PasswordResetTokenModel.user_id)
        )
        result = await self.session.execute(stmt)
        user_id = result.scalar_one_or_none()

        if not user_id:
            return None

        await self.session.commit()
        return user_id
