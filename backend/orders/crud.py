from __future__ import annotations

import json
from uuid import uuid4
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
        branch_code: str,
        iiko_terminal_group_id: str,
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
    async def ensure_iiko_request_order_id(self, *, order_id: int) -> str: ...
    async def rotate_iiko_request_order_id_for_confirmed_retry(self, *, order_id: int) -> Optional[str]: ...
    async def update_iiko_attempt_result(
        self, *, order_id: int, iiko_order_id: Optional[str], iiko_pos_order_id: Optional[str],
        correlation_id: Optional[str], creation_status: Optional[str], error_code: Optional[str],
        error_message: Optional[str],
    ) -> Optional[OrderModel]: ...
    async def increment_iiko_recovery_checks(self, *, order_id: int) -> int: ...
    async def reset_iiko_recovery_checks(self, *, order_id: int) -> None: ...
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
    async def enqueue_missing_paid_iiko_submission_jobs(self, *, limit: int, created_after: Optional[datetime] = None) -> int: ...
    async def claim_due_iiko_submission_jobs(self, *, limit: int, created_after: Optional[datetime] = None) -> Sequence[OrderDeliveryJobModel]: ...
    async def mark_iiko_submission_job_done(self, *, job_id: int) -> None: ...
    async def mark_iiko_submission_job_failed(self, *, job_id: int, error_message: str, next_run_at: datetime) -> None: ...
    async def mark_iiko_submission_job_dead(self, *, job_id: int, error_message: str) -> None: ...
    async def mark_iiko_submission_job_manual_review(self, *, job_id: int, error_message: str) -> None: ...


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
        branch_code: str,
        iiko_terminal_group_id: str,
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
            delivery_street=payload.delivery_street,
            delivery_house=payload.delivery_house,
            delivery_flat=payload.delivery_flat,
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
            branch_code=branch_code,
            iiko_terminal_group_id=iiko_terminal_group_id,
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

    async def ensure_iiko_request_order_id(self, *, order_id: int) -> str:
        request_id = str(uuid4())
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id, OrderModel.iiko_request_order_id.is_(None))
            .values(iiko_request_order_id=request_id, updated_at=func.now())
            .returning(OrderModel.iiko_request_order_id)
        )
        result = await self._session.execute(stmt)
        stored_id = result.scalar_one_or_none()
        if stored_id is None:
            stored_id = await self._session.scalar(
                select(OrderModel.iiko_request_order_id).where(OrderModel.id == order_id)
            )
        await self._session.commit()
        if not stored_id:
            raise ValueError(f"Could not ensure iiko request id for order {order_id}.")
        return str(stored_id)

    async def rotate_iiko_request_order_id_for_confirmed_retry(self, *, order_id: int) -> Optional[str]:
        request_id = str(uuid4())
        stmt = (
            update(OrderModel)
            .where(
                OrderModel.id == order_id,
                OrderModel.iiko_creation_status == "RecoveryPending",
                OrderModel.iiko_recovery_checks >= 3,
            )
            .values(
                iiko_request_order_id=request_id,
                iiko_order_id=None,
                iiko_pos_order_id=None,
                iiko_correlation_id=None,
                iiko_creation_status="LocalPending",
                iiko_recovery_checks=0,
                iiko_error_message=func.concat(
                    "Confirmed absence after recovery; previous_iiko_request_order_id=",
                    OrderModel.iiko_request_order_id,
                    "; previous_iiko_order_id=",
                    func.coalesce(OrderModel.iiko_order_id, ""),
                ),
                updated_at=func.now(),
            )
            .returning(OrderModel.iiko_request_order_id)
        )
        result = await self._session.execute(stmt)
        rotated_id = result.scalar_one_or_none()
        await self._session.commit()
        return str(rotated_id) if rotated_id else None

    async def update_iiko_attempt_result(
        self,
        *,
        order_id: int,
        iiko_order_id: Optional[str],
        iiko_pos_order_id: Optional[str],
        correlation_id: Optional[str],
        creation_status: Optional[str],
        error_code: Optional[str],
        error_message: Optional[str],
    ) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values(
                iiko_order_id=func.coalesce(iiko_order_id, OrderModel.iiko_order_id),
                iiko_pos_order_id=func.coalesce(iiko_pos_order_id, OrderModel.iiko_pos_order_id),
                iiko_correlation_id=func.coalesce(correlation_id, OrderModel.iiko_correlation_id),
                iiko_creation_status=creation_status,
                iiko_error_code=error_code,
                iiko_error_message=error_message,
                iiko_last_error_at=func.now() if error_message else OrderModel.iiko_last_error_at,
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

    async def increment_iiko_recovery_checks(self, *, order_id: int) -> int:
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == order_id)
            .values(iiko_recovery_checks=OrderModel.iiko_recovery_checks + 1, updated_at=func.now())
            .returning(OrderModel.iiko_recovery_checks)
        )
        result = await self._session.execute(stmt)
        count = result.scalar_one_or_none()
        await self._session.commit()
        return int(count or 0)

    async def reset_iiko_recovery_checks(self, *, order_id: int) -> None:
        await self._session.execute(
            update(OrderModel).where(OrderModel.id == order_id).values(iiko_recovery_checks=0, updated_at=func.now())
        )
        await self._session.commit()

    async def claim_iiko_submission(self, *, order_id: int) -> Optional[OrderModel]:
        stmt = (
            update(OrderModel)
            .where(
                OrderModel.id == order_id,
                OrderModel.iiko_order_id.is_(None),
                or_(
                    OrderModel.iiko_creation_status.in_(("LocalPending", "Failed")),
                    (
                        OrderModel.iiko_creation_status == "IikoProcessing"
                    )
                    & (OrderModel.updated_at < func.now() - text("interval '5 minutes'")),
                ),
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
            )
            .order_by(OrderModel.created_at.asc(), OrderModel.id.asc())
            .limit(limit)
        )
        return (await self._session.scalars(stmt)).all()

    async def list_orders_pending_iiko_submission(self, *, limit: int) -> Sequence[OrderModel]:
        stmt = (
            select(OrderModel)
            .where(
                OrderModel.iiko_creation_status.in_(("LocalPending", "Failed", "RecoveryPending")),
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

    async def enqueue_missing_paid_iiko_submission_jobs(self, *, limit: int, created_after: Optional[datetime] = None) -> int:
        safe_limit = max(1, min(limit, 100))
        created_after_filter = "AND pending_payments.created_at >= :created_after" if created_after is not None else ""
        stmt = text(
            f"""
            INSERT INTO order_delivery_jobs (order_id, job_type, status)
            SELECT orders.id, 'send_to_iiko', 'pending'
            FROM orders
            LEFT JOIN pending_payments ON pending_payments.order_id = orders.id
            LEFT JOIN order_delivery_jobs ON order_delivery_jobs.order_id = orders.id
            WHERE orders.iiko_creation_status IN ('LocalPending', 'Failed', 'RecoveryPending')
              AND order_delivery_jobs.id IS NULL
              AND pending_payments.status IN ('succeeded', 'order_failed')
              AND (
                  orders.checkout_type <> 'delivery'
                  OR (
                      orders.delivery_street IS NOT NULL
                      AND btrim(orders.delivery_street) <> ''
                      AND orders.delivery_house IS NOT NULL
                      AND btrim(orders.delivery_house) <> ''
                  )
              )
              {created_after_filter}
            ORDER BY orders.updated_at ASC, orders.id ASC
            LIMIT :limit
            ON CONFLICT (order_id) DO NOTHING
            RETURNING id
            """
        )
        params = {"limit": safe_limit}
        if created_after is not None:
            params["created_after"] = created_after
        result = await self._session.execute(stmt, params)
        created = len(result.fetchall())
        await self._session.commit()
        return created

    async def claim_due_iiko_submission_jobs(self, *, limit: int, created_after: Optional[datetime] = None) -> Sequence[OrderDeliveryJobModel]:
        safe_limit = max(1, min(limit, 100))
        async with self._session.begin():
            stmt = select(OrderDeliveryJobModel).join(OrderModel).where(
                OrderDeliveryJobModel.job_type == "send_to_iiko",
                or_(
                    OrderDeliveryJobModel.status.in_(("pending", "failed")),
                    (
                        OrderDeliveryJobModel.status == "processing"
                    )
                    & (OrderDeliveryJobModel.locked_at < func.now() - text("interval '5 minutes'")),
                ),
                OrderDeliveryJobModel.next_run_at <= func.now(),
                or_(
                    OrderModel.checkout_type != "delivery",
                    (
                        OrderModel.delivery_street.is_not(None)
                        & (func.btrim(OrderModel.delivery_street) != "")
                        & OrderModel.delivery_house.is_not(None)
                        & (func.btrim(OrderModel.delivery_house) != "")
                    ),
                ),
            )
            if created_after is not None:
                stmt = stmt.where(OrderDeliveryJobModel.created_at >= created_after)
            stmt = (
                stmt.order_by(OrderDeliveryJobModel.next_run_at.asc(), OrderDeliveryJobModel.id.asc())
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

    async def mark_iiko_submission_job_dead(self, *, job_id: int, error_message: str) -> None:
        stmt = (
            update(OrderDeliveryJobModel)
            .where(OrderDeliveryJobModel.id == job_id)
            .values(
                status="dead",
                locked_at=None,
                error_message=error_message[:2000],
                updated_at=func.now(),
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def mark_iiko_submission_job_manual_review(self, *, job_id: int, error_message: str) -> None:
        stmt = (
            update(OrderDeliveryJobModel)
            .where(OrderDeliveryJobModel.id == job_id)
            .values(status="manual_review", locked_at=None, error_message=error_message[:2000], updated_at=func.now())
        )
        await self._session.execute(stmt)
        await self._session.commit()
