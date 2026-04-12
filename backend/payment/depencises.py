from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.payment.crud import SqlAlchemyPendingPaymentRepository
from backend.payment.service import YooKassaPaymentService
from db import get_db


def get_pending_payment_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyPendingPaymentRepository:
    return SqlAlchemyPendingPaymentRepository(session)


def get_yookassa_payment_service(
    repository: SqlAlchemyPendingPaymentRepository = Depends(get_pending_payment_repository),
) -> YooKassaPaymentService:
    return YooKassaPaymentService(repository=repository)
