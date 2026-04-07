from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Optional, Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.orders.models import OrderModel
from backend.orders.schemas import OrderCreate


class OrderRepository(Protocol):
    async def create(
        self,
        *,
        user_id: int,
        payload: OrderCreate,
        subtotal_amount: int,
        bonus_spent: int,
        total_amount: int,
        bonus_awarded: int,
    ) -> OrderModel: ...
    async def list_by_user(self, user_id: int) -> Sequence[OrderModel]: ...
    async def get_latest_by_user(self, user_id: int) -> Optional[OrderModel]: ...
    async def count_active_by_user(self, user_id: int) -> int: ...


class SqlAlchemyOrderRepository:
    ACTIVE_STATUSES = {"Новый", "Подтвержден", "Готовится", "В пути"}

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        payload: OrderCreate,
        subtotal_amount: int,
        bonus_spent: int,
        total_amount: int,
        bonus_awarded: int,
    ) -> OrderModel:
        model = OrderModel(
            user_id=user_id,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            checkout_type=payload.checkout_type,
            payment_type=payload.payment_type,
            delivery_address=payload.delivery_address,
            entrance=payload.entrance,
            comment=payload.comment,
            items_json=json.dumps([item.model_dump() for item in payload.items], ensure_ascii=False),
            items_count=sum(item.quantity for item in payload.items),
            cutlery_count=payload.cutlery_count,
            subtotal_amount=subtotal_amount,
            bonus_spent=bonus_spent,
            total_amount=total_amount,
            bonus_awarded=bonus_awarded,
            status="Подтвержден",
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def list_by_user(self, user_id: int) -> Sequence[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.user_id == user_id).order_by(OrderModel.created_at.desc(), OrderModel.id.desc())
        return (await self._session.scalars(stmt)).all()

    async def get_latest_by_user(self, user_id: int) -> Optional[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .order_by(OrderModel.created_at.desc(), OrderModel.id.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def count_active_by_user(self, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(OrderModel)
            .where(OrderModel.user_id == user_id, OrderModel.status.in_(self.ACTIVE_STATUSES))
        )
        return int(await self._session.scalar(stmt) or 0)
