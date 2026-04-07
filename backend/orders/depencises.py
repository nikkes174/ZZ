from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.orders.crud import SqlAlchemyOrderRepository
from backend.orders.service import OrderService
from db import get_db


def get_order_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyOrderRepository:
    return SqlAlchemyOrderRepository(session)


def get_order_service(
    repository: SqlAlchemyOrderRepository = Depends(get_order_repository),
) -> OrderService:
    return OrderService(repository=repository)
