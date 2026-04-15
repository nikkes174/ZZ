from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Optional, Protocol

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.orders.models import OrderModel
from backend.orders.schemas import OrderCreate
from backend.orders.statuses import ACTIVE_ORDER_STATUSES, ORDER_STATUS_PREPARING


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
        idempotency_key: Optional[str] = None,
        iiko_order_id: Optional[str] = None,
        iiko_correlation_id: Optional[str] = None,
        iiko_creation_status: Optional[str] = None,
    ) -> OrderModel: ...
    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[OrderModel]: ...
    async def update_iiko_result(
        self,
        *,
        order_id: int,
        iiko_order_id: Optional[str],
        iiko_correlation_id: Optional[str],
        iiko_creation_status: Optional[str],
    ) -> Optional[OrderModel]: ...
    async def list_by_user(self, user_id: int) -> Sequence[OrderModel]: ...
    async def get_latest_by_user(self, user_id: int) -> Optional[OrderModel]: ...
    async def get_latest_active_by_user(self, user_id: int) -> Optional[OrderModel]: ...
    async def count_active_by_user(self, user_id: int) -> int: ...
    async def list_recent(self, *, limit: int, phone: Optional[str] = None) -> Sequence[OrderModel]: ...
    async def get_by_id(self, order_id: int) -> Optional[OrderModel]: ...
    async def update_status(self, *, order_id: int, status: str) -> Optional[OrderModel]: ...
    async def list_active_iiko_orders(self, *, limit: int) -> Sequence[OrderModel]: ...
    async def update_status_by_iiko_order_id(self, *, iiko_order_id: str, status: str) -> Optional[OrderModel]: ...


class SqlAlchemyOrderRepository:
    ACTIVE_STATUSES = ACTIVE_ORDER_STATUSES

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
        idempotency_key: Optional[str] = None,
        iiko_order_id: Optional[str] = None,
        iiko_correlation_id: Optional[str] = None,
        iiko_creation_status: Optional[str] = None,
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
            idempotency_key=idempotency_key,
            iiko_order_id=iiko_order_id,
            iiko_correlation_id=iiko_correlation_id,
            iiko_creation_status=iiko_creation_status,
            status=ORDER_STATUS_PREPARING,
        )
        self._session.add(model)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            raise
        await self._session.refresh(model)
        return model

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.idempotency_key == idempotency_key)
        return await self._session.scalar(stmt)

    async def update_iiko_result(
        self,
        *,
        order_id: int,
        iiko_order_id: Optional[str],
        iiko_correlation_id: Optional[str],
        iiko_creation_status: Optional[str],
    ) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values(
                iiko_order_id=iiko_order_id,
                iiko_correlation_id=iiko_correlation_id,
                iiko_creation_status=iiko_creation_status,
                updated_at=func.now(),
            )
            .returning(OrderModel)
        )
        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return order

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

    async def get_latest_active_by_user(self, user_id: int) -> Optional[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id, OrderModel.status.in_(self.ACTIVE_STATUSES))
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

    async def list_recent(self, *, limit: int, phone: Optional[str] = None) -> Sequence[OrderModel]:
        stmt = select(OrderModel)
        if phone:
            stmt = stmt.where(OrderModel.customer_phone == phone)
        stmt = stmt.order_by(OrderModel.created_at.desc(), OrderModel.id.desc()).limit(limit)
        return (await self._session.scalars(stmt)).all()

    async def get_by_id(self, order_id: int) -> Optional[OrderModel]:
        stmt = select(OrderModel).where(OrderModel.id == order_id)
        return await self._session.scalar(stmt)

    async def update_status(self, *, order_id: int, status: str) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values(status=status, updated_at=func.now())
            .returning(OrderModel)
        )
        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return order

    async def list_active_iiko_orders(self, *, limit: int) -> Sequence[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(
                OrderModel.status.in_(self.ACTIVE_STATUSES),
                OrderModel.iiko_order_id.is_not(None),
            )
            .order_by(OrderModel.created_at.asc(), OrderModel.id.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def update_status_by_iiko_order_id(self, *, iiko_order_id: str, status: str) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(OrderModel.iiko_order_id == iiko_order_id)
            .values(status=status, updated_at=func.now())
            .returning(OrderModel)
        )
        result = await self._session.execute(stmt)
        order = result.scalar_one_or_none()
        if order is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return order
