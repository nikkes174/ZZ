from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime
from typing import Optional, Protocol

from sqlalchemy import func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.orders.models import OrderDeliveryJobModel, OrderModel
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
    async def claim_iiko_submission(self, *, order_id: int) -> Optional[OrderModel]: ...
    async def list_by_user(self, user_id: int) -> Sequence[OrderModel]: ...
    async def get_latest_by_user(self, user_id: int) -> Optional[OrderModel]: ...
    async def get_latest_active_by_user(self, user_id: int) -> Optional[OrderModel]: ...
    async def count_active_by_user(self, user_id: int) -> int: ...
    async def list_recent(self, *, limit: int, phone: Optional[str] = None) -> Sequence[OrderModel]: ...
    async def get_by_id(self, order_id: int) -> Optional[OrderModel]: ...
    async def update_status(self, *, order_id: int, status: str) -> Optional[OrderModel]: ...
    async def list_active_iiko_orders(self, *, limit: int) -> Sequence[OrderModel]: ...
    async def list_orders_pending_iiko_submission(self, *, limit: int) -> Sequence[OrderModel]: ...
    async def update_status_by_iiko_order_id(self, *, iiko_order_id: str, status: str) -> Optional[OrderModel]: ...
    async def enqueue_iiko_submission_job(self, *, order_id: int) -> None: ...
    async def enqueue_missing_paid_iiko_submission_jobs(self, *, limit: int) -> int: ...
    async def claim_due_iiko_submission_jobs(self, *, limit: int) -> Sequence[OrderDeliveryJobModel]: ...
    async def mark_iiko_submission_job_done(self, *, job_id: int) -> None: ...
    async def mark_iiko_submission_job_failed(self, *, job_id: int, error_message: str, next_run_at: datetime) -> None: ...


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

    async def claim_iiko_submission(self, *, order_id: int) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(
                OrderModel.id == order_id,
                OrderModel.iiko_order_id.is_(None),
                OrderModel.iiko_creation_status.in_(("LocalPending", "Failed")),
            )
            .values(iiko_creation_status="IikoProcessing", updated_at=func.now())
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
                or_(OrderModel.iiko_creation_status.is_(None), OrderModel.iiko_creation_status != "Failed"),
            )
            .order_by(OrderModel.created_at.asc(), OrderModel.id.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def list_orders_pending_iiko_submission(self, *, limit: int) -> Sequence[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(
                OrderModel.iiko_order_id.is_(None),
                OrderModel.iiko_creation_status.in_(("LocalPending", "Failed")),
            )
            .order_by(OrderModel.updated_at.asc(), OrderModel.id.asc())
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

    async def enqueue_iiko_submission_job(self, *, order_id: int) -> None:
        stmt = (
            insert(OrderDeliveryJobModel)
            .values(order_id=order_id, job_type="send_to_iiko", status="pending")
            .on_conflict_do_nothing(index_elements=[OrderDeliveryJobModel.order_id])
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def enqueue_missing_paid_iiko_submission_jobs(self, *, limit: int) -> int:
        stmt = text(
            """
            INSERT INTO order_delivery_jobs (order_id, job_type, status)
            SELECT orders.id, 'send_to_iiko', 'pending'
            FROM pending_payments
            JOIN orders ON orders.id = pending_payments.order_id
            LEFT JOIN order_delivery_jobs ON order_delivery_jobs.order_id = orders.id
            WHERE pending_payments.status = 'succeeded'
              AND pending_payments.order_id IS NOT NULL
              AND orders.iiko_order_id IS NULL
              AND orders.iiko_creation_status IN ('LocalPending', 'Failed')
              AND order_delivery_jobs.id IS NULL
            ORDER BY pending_payments.updated_at ASC, pending_payments.id ASC
            LIMIT :limit
            ON CONFLICT (order_id) DO NOTHING
            RETURNING id
            """
        )
        result = await self._session.execute(stmt, {"limit": max(1, min(limit, 100))})
        created = len(result.fetchall())
        await self._session.commit()
        return created

    async def claim_due_iiko_submission_jobs(self, *, limit: int) -> Sequence[OrderDeliveryJobModel]:
        safe_limit = max(1, min(limit, 100))
        async with self._session.begin():
            stmt = (
                select(OrderDeliveryJobModel)
                .where(
                    OrderDeliveryJobModel.job_type == "send_to_iiko",
                    OrderDeliveryJobModel.status.in_(("pending", "failed")),
                    OrderDeliveryJobModel.next_run_at <= func.now(),
                )
                .order_by(OrderDeliveryJobModel.next_run_at.asc(), OrderDeliveryJobModel.id.asc())
                .limit(safe_limit)
                .with_for_update(skip_locked=True)
            )
            jobs = list((await self._session.scalars(stmt)).all())
            if not jobs:
                return []

            await self._session.execute(
                update(OrderDeliveryJobModel)
                .where(OrderDeliveryJobModel.id.in_([job.id for job in jobs]))
                .values(
                    status="processing",
                    attempts=OrderDeliveryJobModel.attempts + 1,
                    locked_at=func.now(),
                    updated_at=func.now(),
                    error_message=None,
                )
            )
            return jobs

    async def mark_iiko_submission_job_done(self, *, job_id: int) -> None:
        stmt = (
            update(OrderDeliveryJobModel)
            .where(OrderDeliveryJobModel.id == job_id)
            .values(status="done", locked_at=None, error_message=None, updated_at=func.now())
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def mark_iiko_submission_job_failed(self, *, job_id: int, error_message: str, next_run_at: datetime) -> None:
        stmt = (
            update(OrderDeliveryJobModel)
            .where(OrderDeliveryJobModel.id == job_id)
            .values(
                status="failed",
                locked_at=None,
                error_message=error_message[:2000],
                next_run_at=next_run_at,
                updated_at=func.now(),
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()
