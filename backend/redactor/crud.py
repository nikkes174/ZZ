from __future__ import annotations

from collections.abc import Sequence
from typing import Optional, Protocol

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.redactor.models import MenuItemModel
from backend.redactor.schemas import MenuItemCreate, MenuItemUpdate


class MenuItemRepository(Protocol):
    async def list(
        self,
        *,
        limit: int,
        offset: int,
        include_inactive: bool,
    ) -> tuple[Sequence[MenuItemModel], int]: ...
    async def search_catalog(
        self,
        *,
        query: str,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[MenuItemModel], int]: ...

    async def get(self, item_id: int) -> Optional[MenuItemModel]: ...
    async def create(self, payload: MenuItemCreate) -> MenuItemModel: ...
    async def update(self, item_id: int, payload: MenuItemUpdate) -> Optional[MenuItemModel]: ...
    async def hard_delete(self, item_id: int, version: int) -> Optional[MenuItemModel]: ...
    async def count_all(self) -> int: ...
    async def seed_defaults(self, items: list[MenuItemCreate]) -> None: ...


class SqlAlchemyMenuItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        include_inactive: bool,
    ) -> tuple[Sequence[MenuItemModel], int]:
        filters = [MenuItemModel.sync_source == "iiko", MenuItemModel.is_published.is_(True)]
        if not include_inactive:
            filters.append(MenuItemModel.is_active.is_(True))

        total_stmt = select(func.count()).select_from(MenuItemModel)
        if filters:
            total_stmt = total_stmt.where(*filters)

        items_stmt = (
            select(MenuItemModel)
            .where(*filters)
            .order_by(MenuItemModel.sort_order.asc(), MenuItemModel.id.asc())
            .limit(limit)
            .offset(offset)
        )

        total = int(await self._session.scalar(total_stmt) or 0)
        items = (await self._session.scalars(items_stmt)).all()
        return items, total

    async def search_catalog(
        self,
        *,
        query: str,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[MenuItemModel], int]:
        filters = [
            MenuItemModel.sync_source == "iiko",
            MenuItemModel.is_active.is_(True),
            MenuItemModel.is_deleted_in_iiko.is_(False),
        ]
        normalized_query = query.strip()
        if normalized_query:
            pattern = f"%{normalized_query}%"
            filters.append(
                or_(
                    MenuItemModel.title.ilike(pattern),
                    MenuItemModel.site_title.ilike(pattern),
                    MenuItemModel.iiko_category_name.ilike(pattern),
                    MenuItemModel.category.ilike(pattern),
                )
            )

        total_stmt = select(func.count()).select_from(MenuItemModel).where(*filters)
        items_stmt = (
            select(MenuItemModel)
            .where(*filters)
            .order_by(
                MenuItemModel.is_published.desc(),
                MenuItemModel.is_active.desc(),
                MenuItemModel.title.asc(),
            )
            .limit(limit)
            .offset(offset)
        )

        total = int(await self._session.scalar(total_stmt) or 0)
        items = (await self._session.scalars(items_stmt)).all()
        return items, total

    async def get(self, item_id: int) -> Optional[MenuItemModel]:
        stmt = select(MenuItemModel).where(MenuItemModel.id == item_id, MenuItemModel.sync_source == "iiko")
        return await self._session.scalar(stmt)

    async def create(self, payload: MenuItemCreate) -> MenuItemModel:
        model = MenuItemModel(**payload.model_dump())
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def update(self, item_id: int, payload: MenuItemUpdate) -> Optional[MenuItemModel]:
        values = payload.model_dump(exclude_unset=True, exclude={"version"})
        if not values:
            return await self.get(item_id)

        stmt = (
            update(MenuItemModel)
            .where(MenuItemModel.id == item_id, MenuItemModel.version == payload.version)
            .values(**values, version=MenuItemModel.version + 1)
            .returning(MenuItemModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return model

    async def hard_delete(self, item_id: int, version: int) -> Optional[MenuItemModel]:
        stmt = (
            delete(MenuItemModel)
            .where(MenuItemModel.id == item_id, MenuItemModel.version == version)
            .returning(MenuItemModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return model

    async def count_all(self) -> int:
        return int(await self._session.scalar(select(func.count()).select_from(MenuItemModel)) or 0)

    async def seed_defaults(self, items: list[MenuItemCreate]) -> None:
        if not items:
            return
        if await self.count_all():
            return

        self._session.add_all(MenuItemModel(**item.model_dump()) for item in items)
        await self._session.commit()
