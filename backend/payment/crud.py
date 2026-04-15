from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.payment.models import PendingPaymentModel


class SqlAlchemyPendingPaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pending(
        self,
        *,
        user_id: int,
        amount: int,
        payload_json: str,
    ) -> PendingPaymentModel:
        model = PendingPaymentModel(
            user_id=user_id,
            amount=amount,
            payload_json=payload_json,
            status="pending",
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def attach_yookassa_payment(
        self,
        *,
        pending_payment_id: int,
        yookassa_payment_id: str,
        confirmation_url: str,
        status: str,
    ) -> Optional[PendingPaymentModel]:
        stmt = (
            update(PendingPaymentModel)
            .where(PendingPaymentModel.id == pending_payment_id)
            .values(
                yookassa_payment_id=yookassa_payment_id,
                confirmation_url=confirmation_url,
                status=status,
                updated_at=func.now(),
            )
            .returning(PendingPaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None
        await self._session.commit()
        return model

    async def get_by_yookassa_payment_id(self, payment_id: str) -> Optional[PendingPaymentModel]:
        stmt = select(PendingPaymentModel).where(PendingPaymentModel.yookassa_payment_id == payment_id)
        return await self._session.scalar(stmt)

    async def claim_for_order_creation(
        self,
        *,
        pending_payment_id: int,
    ) -> Optional[PendingPaymentModel]:
        stmt = (
            update(PendingPaymentModel)
            .where(
                PendingPaymentModel.id == pending_payment_id,
                PendingPaymentModel.order_id.is_(None),
                PendingPaymentModel.status != "processing",
            )
            .values(status="processing", error_message=None, updated_at=func.now())
            .returning(PendingPaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None

        await self._session.commit()
        return model

    async def mark_order_created(
        self,
        *,
        pending_payment_id: int,
        order_id: int,
    ) -> Optional[PendingPaymentModel]:
        stmt = (
            update(PendingPaymentModel)
            .where(PendingPaymentModel.id == pending_payment_id)
            .values(status="succeeded", order_id=order_id, error_message=None, updated_at=func.now())
            .returning(PendingPaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None
        await self._session.commit()
        return model

    async def mark_failed(
        self,
        *,
        pending_payment_id: int,
        status: str,
        error_message: str,
    ) -> Optional[PendingPaymentModel]:
        stmt = (
            update(PendingPaymentModel)
            .where(PendingPaymentModel.id == pending_payment_id)
            .values(status=status, error_message=error_message, updated_at=func.now())
            .returning(PendingPaymentModel)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            await self._session.rollback()
            return None
        await self._session.commit()
        return model
