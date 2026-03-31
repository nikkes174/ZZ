from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.redactor.crud import SqlAlchemyMenuItemRepository
from backend.redactor.service import MenuItemService
from db import get_db


def get_menu_item_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyMenuItemRepository:
    return SqlAlchemyMenuItemRepository(session)


def get_menu_item_service(
    repository: SqlAlchemyMenuItemRepository = Depends(get_menu_item_repository),
) -> MenuItemService:
    return MenuItemService(repository=repository)
