from __future__ import annotations

from dataclasses import dataclass

from config import REDACTOR_PAGE_LIMIT

from backend.redactor.crud import MenuItemRepository
from backend.redactor.schemas import (
    MenuItemCatalogPage,
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

    def _to_read_model(self, item) -> MenuItemRead:
        payload = {
            "id": item.id,
            "title": item.site_title or item.title,
            "description": item.site_description or item.description,
            "iiko_title": item.title,
            "iiko_description": item.description,
            "price": item.price,
            "category": item.category,
            "accent": item.accent,
            "badge": item.badge,
            "image_path": item.image_path,
            "sort_order": item.sort_order,
            "is_active": item.is_active,
            "is_published": item.is_published,
            "version": item.version,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        return MenuItemRead.model_validate(payload)

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
            items=[self._to_read_model(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
        )

    async def list_storefront_items(self) -> list[MenuItemRead]:
        items = await self.repository.list_storefront()
        return [self._to_read_model(item) for item in items]

    async def search_catalog_items(
        self,
        *,
        query: str = "",
        limit: int = 20,
        offset: int = 0,
    ) -> MenuItemCatalogPage:
        safe_limit = max(1, min(limit, REDACTOR_PAGE_LIMIT))
        safe_offset = max(0, offset)
        items, total = await self.repository.search_catalog(
            query=query,
            limit=safe_limit,
            offset=safe_offset,
        )
        return MenuItemCatalogPage(
            items=[self._to_read_model(item) for item in items],
            total=total,
            limit=safe_limit,
            offset=safe_offset,
            query=query,
        )

    async def get_item(self, item_id: int) -> MenuItemRead:
        item = await self.repository.get(item_id)
        if item is None:
            raise MenuItemNotFoundError(item_id)
        return self._to_read_model(item)

    async def create_item(self, payload: MenuItemCreate) -> MenuItemRead:
        item = await self.repository.create(payload)
        return self._to_read_model(item)

    async def update_item(self, item_id: int, payload: MenuItemUpdate) -> MenuItemRead:
        item = await self.repository.update(item_id, payload)
        if item is not None:
            return self._to_read_model(item)

        existing = await self.repository.get(item_id)
        if existing is None:
            raise MenuItemNotFoundError(item_id)
        raise MenuItemConflictError(item_id)

    async def delete_item(self, item_id: int, payload: MenuItemDelete) -> MenuItemRead:
        item = await self.repository.hard_delete(item_id, payload.version)
        if item is not None:
            return self._to_read_model(item)

        existing = await self.repository.get(item_id)
        if existing is None:
            raise MenuItemNotFoundError(item_id)
        raise MenuItemConflictError(item_id)

    async def ensure_seed_data(self, items: list[MenuItemCreate]) -> None:
        await self.repository.seed_defaults(items)
