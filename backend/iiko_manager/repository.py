from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import logging
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.redactor.models import MenuItemModel


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CatalogSyncItem:
    iiko_product_id: str
    iiko_group_id: Optional[str]
    iiko_category_name: Optional[str]
    iiko_parent_group_id: Optional[str]
    iiko_terminal_group_id: str
    title: str
    description: str
    category: str
    price_from_iiko: Optional[int]
    is_active: bool
    is_deleted_in_iiko: bool
    sync_hash: str


@dataclass(frozen=True)
class CatalogSyncResult:
    created: int
    updated: int
    deactivated: int


class IikoCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def sync_items(
        self,
        *,
        items: Sequence[CatalogSyncItem],
        synced_at: datetime,
        terminal_group_id: str,
    ) -> CatalogSyncResult:
        logger.info(
            "Repository sync started. terminal_group_id=%s items=%s synced_at=%s",
            terminal_group_id,
            len(items),
            synced_at.isoformat(),
        )
        existing = await self._get_existing_by_product_ids(
            product_ids=(item.iiko_product_id for item in items),
            terminal_group_id=terminal_group_id,
        )
        logger.info("Loaded existing iiko menu items from database. count=%s", len(existing))

        created = 0
        updated = 0
        seen_product_ids: set[str] = set()

        for item in items:
            seen_product_ids.add(item.iiko_product_id)
            model = existing.get(item.iiko_product_id)
            if model is None:
                self._session.add(self._build_model(item=item, synced_at=synced_at))
                created += 1
                continue

            if not self._needs_update(model=model, item=item):
                continue

            self._apply_remote_state(model=model, item=item, synced_at=synced_at)
            updated += 1

        deactivated = await self._deactivate_missing_items(
            active_product_ids=seen_product_ids,
            synced_at=synced_at,
            terminal_group_id=terminal_group_id,
        )
        await self._session.commit()
        logger.info(
            "Repository sync committed. created=%s updated=%s deactivated=%s",
            created,
            updated,
            deactivated,
        )
        return CatalogSyncResult(created=created, updated=updated, deactivated=deactivated)

    async def _get_existing_by_product_ids(
        self,
        *,
        product_ids: Iterable[str],
        terminal_group_id: str,
    ) -> dict[str, MenuItemModel]:
        ids = list(dict.fromkeys(product_ids))
        if not ids:
            return {}

        stmt: Select[tuple[MenuItemModel]] = select(MenuItemModel).where(
            MenuItemModel.iiko_product_id.in_(ids),
            MenuItemModel.iiko_terminal_group_id == terminal_group_id,
        )
        rows = (await self._session.scalars(stmt)).all()
        return {row.iiko_product_id: row for row in rows if row.iiko_product_id}

    async def _deactivate_missing_items(
        self,
        *,
        active_product_ids: set[str],
        synced_at: datetime,
        terminal_group_id: Optional[str],
    ) -> int:
        if terminal_group_id is None:
            return 0

        stmt = (
            update(MenuItemModel)
            .where(
                MenuItemModel.sync_source == "iiko",
                MenuItemModel.iiko_terminal_group_id == terminal_group_id,
                MenuItemModel.iiko_product_id.is_not(None),
                MenuItemModel.is_deleted_in_iiko.is_(False),
            )
            .values(
                is_active=False,
                is_deleted_in_iiko=True,
                last_synced_at=synced_at,
                version=MenuItemModel.version + 1,
            )
        )
        if active_product_ids:
            stmt = stmt.where(MenuItemModel.iiko_product_id.not_in(active_product_ids))

        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

    def _build_model(self, *, item: CatalogSyncItem, synced_at: datetime) -> MenuItemModel:
        accent = self._default_accent(item.iiko_group_id or item.category)
        return MenuItemModel(
            sync_source="iiko",
            iiko_product_id=item.iiko_product_id,
            iiko_group_id=item.iiko_group_id,
            iiko_category_name=item.iiko_category_name,
            iiko_parent_group_id=item.iiko_parent_group_id,
            iiko_terminal_group_id=item.iiko_terminal_group_id,
            title=item.title,
            description=item.description,
            price=item.price_from_iiko or 0,
            price_from_iiko=item.price_from_iiko,
            category=item.category,
            accent=accent,
            badge=None,
            image_path=None,
            sort_order=0,
            is_active=item.is_active,
            is_deleted_in_iiko=item.is_deleted_in_iiko,
            sync_hash=item.sync_hash,
            last_synced_at=synced_at,
        )

    def _needs_update(self, *, model: MenuItemModel, item: CatalogSyncItem) -> bool:
        return any(
            (
                model.sync_source != "iiko",
                model.iiko_group_id != item.iiko_group_id,
                model.iiko_category_name != item.iiko_category_name,
                model.iiko_parent_group_id != item.iiko_parent_group_id,
                model.iiko_terminal_group_id != item.iiko_terminal_group_id,
                model.title != item.title,
                model.description != item.description,
                model.price_from_iiko != item.price_from_iiko,
                model.price != (item.price_from_iiko or 0),
                model.is_active != item.is_active,
                model.is_deleted_in_iiko != item.is_deleted_in_iiko,
                model.sync_hash != item.sync_hash,
            )
        )

    def _apply_remote_state(self, *, model: MenuItemModel, item: CatalogSyncItem, synced_at: datetime) -> None:
        model.sync_source = "iiko"
        model.iiko_group_id = item.iiko_group_id
        model.iiko_category_name = item.iiko_category_name
        model.iiko_parent_group_id = item.iiko_parent_group_id
        model.iiko_terminal_group_id = item.iiko_terminal_group_id
        model.title = item.title
        model.description = item.description
        model.price_from_iiko = item.price_from_iiko
        model.price = item.price_from_iiko or 0
        model.is_active = item.is_active
        model.is_deleted_in_iiko = item.is_deleted_in_iiko
        model.sync_hash = item.sync_hash
        model.last_synced_at = synced_at
        model.version += 1

    def _default_accent(self, seed: str) -> str:
        palette = ("#e85424", "#d9a35f", "#5ab6a6", "#6da4ff", "#ef7b5c", "#9ccf7f")
        index = sum(ord(char) for char in seed) % len(palette)
        return palette[index]
