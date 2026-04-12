from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.user.crud import SqlAlchemyUserRepository
from backend.user.service import UserService
from db import get_db


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_user_service(
    repository: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository=repository)
