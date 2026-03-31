from __future__ import annotations

from dataclasses import dataclass

from config import REDACTOR_PAGE_LIMIT

from backend.redactor.crud import MenuItemRepository
from backend.redactor.schemas import (
    MenuItemCreate,
    MenuItemDelete,
    MenuItemRead,
    MenuItemsPage,
    MenuItemUpdate,
)


class MenuItemNotFoundError(Exception):
    pass


class MenuItemConflictError(Exception):
    pass


@dataclass
class MenuItemService:
    repository: MenuItemRepository

    async def list_items(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        include_inactive: bool = False,
    ) -> MenuItemsPage:
        safe_limit = max(1, min(limit, REDACTOR_PAGE_LIMIT))
        safe_offset = max(0, offset)
        items, total = await self.repository.list(
            limit=safe_limit,
            offset=safe_offset,
            include_inactive=include_inactive,
        )
        return MenuItemsPage(
            items=[MenuItemRead.model_validate(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    async def get_item(self, item_id: int) -> MenuItemRead:
        item = await self.repository.get(item_id)
        if item is None:
            raise MenuItemNotFoundError(item_id)
        return MenuItemRead.model_validate(item)

    async def create_item(self, payload: MenuItemCreate) -> MenuItemRead:
        item = await self.repository.create(payload)
        return MenuItemRead.model_validate(item)

    async def update_item(self, item_id: int, payload: MenuItemUpdate) -> MenuItemRead:
        item = await self.repository.update(item_id, payload)
        if item is not None:
            return MenuItemRead.model_validate(item)

        existing = await self.repository.get(item_id)
        if existing is None:
            raise MenuItemNotFoundError(item_id)
        raise MenuItemConflictError(item_id)

    async def delete_item(self, item_id: int, payload: MenuItemDelete) -> MenuItemRead:
        item = await self.repository.hard_delete(item_id, payload.version)
        if item is not None:
            return MenuItemRead.model_validate(item)

        existing = await self.repository.get(item_id)
        if existing is None:
            raise MenuItemNotFoundError(item_id)
        raise MenuItemConflictError(item_id)

    async def ensure_seed_data(self, items: list[MenuItemCreate]) -> None:
        await self.repository.seed_defaults(items)
