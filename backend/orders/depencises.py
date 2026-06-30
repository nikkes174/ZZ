from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.iiko_manager.client import IikoApiClient
from backend.orders.crud import SqlAlchemyOrderRepository
from backend.orders.iiko import IikoOrderGateway
from backend.orders.service import OrderService
from backend.redactor.crud import SqlAlchemyMenuItemRepository
from config import (
    API_IIKO,
    IIKO_BASE_URL,
    IIKO_ONLINE_PAYMENT_TYPE_ID,
    IIKO_ONLINE_PAYMENT_TYPE_KIND,
    IIKO_ORDER_SOURCE_KEY,
    IIKO_ORDER_TIMEOUT_SECONDS,
    IIKO_ORGANIZATION_ID,
)
from db import get_db


def get_order_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyOrderRepository:
    return SqlAlchemyOrderRepository(session)


def get_order_menu_item_repository(
    session: AsyncSession = Depends(get_db),
) -> SqlAlchemyMenuItemRepository:
    return SqlAlchemyMenuItemRepository(session)


def get_iiko_order_gateway() -> IikoOrderGateway:
    return IikoOrderGateway(
        client=IikoApiClient(
            api_login=API_IIKO or "",
            base_url=IIKO_BASE_URL,
            timeout_seconds=IIKO_ORDER_TIMEOUT_SECONDS,
        ),
        organization_id=IIKO_ORGANIZATION_ID,
        source_key=IIKO_ORDER_SOURCE_KEY,
        online_payment_type_id=IIKO_ONLINE_PAYMENT_TYPE_ID,
        online_payment_type_kind=IIKO_ONLINE_PAYMENT_TYPE_KIND,
    )


def get_order_service(
    repository: SqlAlchemyOrderRepository = Depends(get_order_repository),
    menu_item_repository: SqlAlchemyMenuItemRepository = Depends(get_order_menu_item_repository),
    iiko_order_gateway: IikoOrderGateway = Depends(get_iiko_order_gateway),
) -> OrderService:
    return OrderService(
        repository=repository,
        menu_item_repository=menu_item_repository,
        iiko_order_gateway=iiko_order_gateway,
    )
