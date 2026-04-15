from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError

from backend.iiko_manager.client import IikoApiClient, IikoClientError
from backend.orders.crud import OrderRepository
from backend.orders.iiko import IikoOrderError, IikoOrderGateway, IikoOrderItem
from backend.orders.schemas import AdminOrdersPage, OrderCreate, OrderItemPayload, OrderRead, UserOrdersPage
from backend.orders.statuses import (
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_DELIVERED,
    ORDER_STATUS_DELIVERY_SENT,
    ORDER_STATUS_PICKUP_DONE,
    ORDER_STATUS_PICKUP_READY,
    ORDER_STATUS_PREPARING,
    get_allowed_statuses,
)
from backend.redactor.crud import MenuItemRepository
from config import API_IIKO
logger = logging.getLogger(__name__)
BONUS_AWARD_PERCENT = 5


class OrderValidationError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class NormalizedOrderItem:
    order_item: OrderItemPayload
    iiko_product_id: str


@dataclass(frozen=True)
class PreparedOrder:
    payload: OrderCreate
    normalized_items: list[NormalizedOrderItem]
    subtotal_amount: int
    total_amount: int


@dataclass(frozen=True)
class OrderStatusSyncResult:
    checked: int = 0
    updated: int = 0


@dataclass(frozen=True)
class ClaimedOrder:
    order: OrderRead
    prepared_order: Optional[PreparedOrder]
    is_owner: bool


@dataclass
class IikoOrderStatusSyncService:
    repository: OrderRepository
    client: IikoApiClient
    organization_id: Optional[str]
    limit: int = 50

    async def sync(self) -> OrderStatusSyncResult:
        if not self.client.api_login:
            logger.info("Skipping iiko order status sync because API_IIKO is not configured.")
            return OrderStatusSyncResult()

        active_orders = await self.repository.list_active_iiko_orders(limit=self.limit)
        orders_by_iiko_id = {
            str(order.iiko_order_id): order
            for order in active_orders
            if order.iiko_order_id
        }
        if not orders_by_iiko_id:
            return OrderStatusSyncResult()

        token = await self.client.get_access_token()
        organization_id = await self._resolve_organization_id(token=token)
        iiko_orders = await self.client.get_delivery_orders_by_ids(
            token=token,
            organization_id=organization_id,
            order_ids=list(orders_by_iiko_id),
        )

        updated = 0
        for iiko_order in iiko_orders:
            iiko_order_id = self._extract_iiko_order_id(iiko_order)
            if not iiko_order_id:
                continue

            local_order = orders_by_iiko_id.get(iiko_order_id)
            if local_order is None:
                continue

            iiko_status = self._extract_iiko_status(iiko_order)
            next_status = self._map_iiko_status(iiko_status=iiko_status, checkout_type=local_order.checkout_type)
            if not next_status or next_status == local_order.status:
                continue

            await self.repository.update_status_by_iiko_order_id(
                iiko_order_id=iiko_order_id,
                status=next_status,
            )
            updated += 1
            logger.info(
                "Synced order status from iiko. order_id=%s iiko_order_id=%s iiko_status=%s status=%s",
                local_order.id,
                iiko_order_id,
                iiko_status,
                next_status,
            )

        return OrderStatusSyncResult(checked=len(orders_by_iiko_id), updated=updated)

    async def _resolve_organization_id(self, *, token: str) -> str:
        if self.organization_id:
            return self.organization_id

        try:
            organizations = await self.client.get_organizations(token=token)
        except IikoClientError as exc:
            raise OrderValidationError(str(exc)) from exc

        if len(organizations) != 1:
            raise OrderValidationError("IIKO_ORGANIZATION_ID is required for order status sync.")

        organization_id = organizations[0].get("id")
        if not organization_id:
            raise OrderValidationError("iiko did not return a valid organization id.")
        return str(organization_id)

    def _extract_iiko_order_id(self, payload: dict[str, Any]) -> Optional[str]:
        for candidate in (
            payload.get("id"),
            payload.get("orderId"),
            (payload.get("order") or {}).get("id") if isinstance(payload.get("order"), dict) else None,
            (payload.get("orderInfo") or {}).get("id") if isinstance(payload.get("orderInfo"), dict) else None,
        ):
            if candidate:
                return str(candidate)
        return None

    def _extract_iiko_status(self, payload: dict[str, Any]) -> Optional[str]:
        candidates: list[Any] = [
            payload.get("status"),
            payload.get("deliveryStatus"),
        ]
        for key in ("order", "orderInfo"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                candidates.extend(
                    [
                        nested.get("status"),
                        nested.get("deliveryStatus"),
                    ]
                )
        candidates.append(payload.get("creationStatus"))
        for key in ("order", "orderInfo"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                candidates.append(nested.get("creationStatus"))

        for candidate in candidates:
            if candidate:
                return str(candidate)
        return None

    def _map_iiko_status(self, *, iiko_status: Optional[str], checkout_type: str) -> Optional[str]:
        if not iiko_status:
            return None

        normalized = iiko_status.strip().lower()
        if normalized in {"cancelled", "canceled", "deleted"}:
            return ORDER_STATUS_CANCELLED
        if normalized in {"delivered"}:
            return ORDER_STATUS_DELIVERED if checkout_type == "delivery" else ORDER_STATUS_PICKUP_DONE
        if normalized in {"closed"}:
            return ORDER_STATUS_PICKUP_DONE if checkout_type == "pickup" else ORDER_STATUS_DELIVERED
        if normalized in {"onway", "on_way", "on way"}:
            return ORDER_STATUS_DELIVERY_SENT if checkout_type == "delivery" else ORDER_STATUS_PICKUP_READY
        if normalized in {"cookingcompleted", "cooking_completed", "cooking completed", "ready", "waiting"}:
            return ORDER_STATUS_PICKUP_READY if checkout_type == "pickup" else ORDER_STATUS_DELIVERY_SENT
        if normalized in {
            "success",
            "inprogress",
            "in_progress",
            "unconfirmed",
            "waitcooking",
            "wait_cooking",
            "readyforcooking",
            "ready_for_cooking",
            "cookingstarted",
            "cooking_started",
            "new",
        }:
            return ORDER_STATUS_PREPARING

        logger.info("Unknown iiko order status received. iiko_status=%s", iiko_status)
        return None


@dataclass
class OrderService:
    repository: OrderRepository
    menu_item_repository: MenuItemRepository
    iiko_order_gateway: IikoOrderGateway

    def _calculate_bonus_awarded(self, total_amount: int) -> int:
        return max(0, total_amount * BONUS_AWARD_PERCENT // 100)

    async def claim_order_creation(
        self,
        *,
        user_id: int,
        payload: OrderCreate,
        available_bonus_balance: int,
        idempotency_key: str,
    ) -> ClaimedOrder:
        normalized_idempotency_key = idempotency_key.strip()[:128]
        if not normalized_idempotency_key:
            raise OrderValidationError("Order idempotency key is required.")

        existing_order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
        if existing_order is not None:
            return ClaimedOrder(
                order=self._to_read(existing_order),
                prepared_order=None,
                is_owner=False,
            )

        prepared_order = await self.prepare_order(
            payload=payload,
            available_bonus_balance=available_bonus_balance,
        )
        bonus_awarded = self._calculate_bonus_awarded(prepared_order.total_amount)
        try:
            local_order = await self.repository.create(
                user_id=user_id,
                payload=prepared_order.payload,
                subtotal_amount=prepared_order.subtotal_amount,
                bonus_spent=prepared_order.payload.bonus_spent,
                total_amount=prepared_order.total_amount,
                bonus_awarded=bonus_awarded,
                idempotency_key=normalized_idempotency_key,
                iiko_creation_status="LocalPending",
            )
        except IntegrityError:
            existing_order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
            if existing_order is not None:
                return ClaimedOrder(
                    order=self._to_read(existing_order),
                    prepared_order=None,
                    is_owner=False,
                )
            raise

        return ClaimedOrder(
            order=self._to_read(local_order),
            prepared_order=prepared_order,
            is_owner=True,
        )

    async def submit_claimed_order(self, *, order_id: int, prepared_order: PreparedOrder) -> OrderRead:
        try:
            iiko_result = await self.iiko_order_gateway.submit_order(
                payload=prepared_order.payload,
                items=[
                    IikoOrderItem(
                        product_id=item.iiko_product_id,
                        title=item.order_item.title,
                        price=item.order_item.price,
                        quantity=item.order_item.quantity,
                    )
                    for item in prepared_order.normalized_items
                ],
                total_amount=prepared_order.total_amount,
            )
        except IikoOrderError as exc:
            await self.repository.update_iiko_result(
                order_id=order_id,
                iiko_order_id=None,
                iiko_correlation_id=None,
                iiko_creation_status="Failed",
            )
            raise OrderValidationError(str(exc)) from exc

        order = await self.repository.update_iiko_result(
            order_id=order_id,
            iiko_order_id=iiko_result.get("iiko_order_id") or None,
            iiko_correlation_id=iiko_result.get("correlation_id") or None,
            iiko_creation_status=iiko_result.get("creation_status") or None,
        )
        if order is None:
            raise OrderNotFoundError(order_id)
        return self._to_read(order)

    async def prepare_order(self, *, payload: OrderCreate, available_bonus_balance: int) -> PreparedOrder:
        normalized_items = await self._normalize_order_items(payload)
        subtotal_amount = sum(item.order_item.price * item.order_item.quantity for item in normalized_items)
        if subtotal_amount <= 0:
            raise OrderValidationError("Сумма заказа должна быть больше нуля.")
        if payload.checkout_type == "delivery" and not (payload.delivery_address or "").strip():
            raise OrderValidationError("Укажите адрес доставки.")
        if payload.bonus_spent > available_bonus_balance:
            raise OrderValidationError("Недостаточно бонусов для списания.")
        if payload.bonus_spent > subtotal_amount:
            raise OrderValidationError("Нельзя списать бонусов больше суммы заказа.")

        normalized_payload = payload.model_copy(update={"items": [item.order_item for item in normalized_items]})
        total_amount = subtotal_amount - normalized_payload.bonus_spent
        return PreparedOrder(
            payload=normalized_payload,
            normalized_items=normalized_items,
            subtotal_amount=subtotal_amount,
            total_amount=total_amount,
        )

    async def create_order(
        self,
        *,
        user_id: int,
        payload: OrderCreate,
        available_bonus_balance: int,
        idempotency_key: Optional[str] = None,
    ) -> OrderRead:
        normalized_idempotency_key = (idempotency_key or "").strip()[:128] or None
        if normalized_idempotency_key:
            existing_order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
            if existing_order is not None:
                return self._to_read(existing_order)

        prepared_order = await self.prepare_order(
            payload=payload,
            available_bonus_balance=available_bonus_balance,
        )

        bonus_awarded = self._calculate_bonus_awarded(prepared_order.total_amount)
        local_order = None
        if normalized_idempotency_key:
            try:
                local_order = await self.repository.create(
                    user_id=user_id,
                    payload=prepared_order.payload,
                    subtotal_amount=prepared_order.subtotal_amount,
                    bonus_spent=prepared_order.payload.bonus_spent,
                    total_amount=prepared_order.total_amount,
                    bonus_awarded=bonus_awarded,
                    idempotency_key=normalized_idempotency_key,
                    iiko_creation_status="LocalPending",
                )
            except IntegrityError:
                existing_order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
                if existing_order is not None:
                    return self._to_read(existing_order)
                raise

        try:
            iiko_result = await self.iiko_order_gateway.submit_order(
                payload=prepared_order.payload,
                items=[
                    IikoOrderItem(
                        product_id=item.iiko_product_id,
                        title=item.order_item.title,
                        price=item.order_item.price,
                        quantity=item.order_item.quantity,
                    )
                    for item in prepared_order.normalized_items
                ],
                total_amount=prepared_order.total_amount,
            )
        except IikoOrderError as exc:
            if local_order is not None:
                await self.repository.update_iiko_result(
                    order_id=local_order.id,
                    iiko_order_id=None,
                    iiko_correlation_id=None,
                    iiko_creation_status="Failed",
                )
            raise OrderValidationError(str(exc)) from exc

        if local_order is not None:
            order = await self.repository.update_iiko_result(
                order_id=local_order.id,
                iiko_order_id=iiko_result.get("iiko_order_id") or None,
                iiko_correlation_id=iiko_result.get("correlation_id") or None,
                iiko_creation_status=iiko_result.get("creation_status") or None,
            )
            if order is None:
                raise OrderNotFoundError(local_order.id)
        else:
            order = await self.repository.create(
                user_id=user_id,
                payload=prepared_order.payload,
                subtotal_amount=prepared_order.subtotal_amount,
                bonus_spent=prepared_order.payload.bonus_spent,
                total_amount=prepared_order.total_amount,
                bonus_awarded=bonus_awarded,
                idempotency_key=normalized_idempotency_key,
                iiko_order_id=iiko_result.get("iiko_order_id") or None,
                iiko_correlation_id=iiko_result.get("correlation_id") or None,
                iiko_creation_status=iiko_result.get("creation_status") or None,
            )
        return self._to_read(order)

    async def list_user_orders(self, user_id: int) -> UserOrdersPage:
        orders = await self.repository.list_by_user(user_id)
        return UserOrdersPage(items=[self._to_read(order) for order in orders])

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[OrderRead]:
        normalized_idempotency_key = idempotency_key.strip()[:128]
        if not normalized_idempotency_key:
            return None
        order = await self.repository.get_by_idempotency_key(normalized_idempotency_key)
        return self._to_read(order) if order is not None else None

    async def get_latest_status(self, user_id: int) -> Optional[str]:
        latest_order = await self.repository.get_latest_active_by_user(user_id)
        if latest_order is None:
            latest_order = await self.repository.get_latest_by_user(user_id)
        return latest_order.status if latest_order else None

    async def count_active_orders(self, user_id: int) -> int:
        return await self.repository.count_active_by_user(user_id)

    async def list_admin_orders(self, *, limit: int = 30, phone: Optional[str] = None) -> AdminOrdersPage:
        safe_limit = max(1, min(limit, 100))
        normalized_phone = (phone or "").strip() or None
        orders = await self.repository.list_recent(limit=safe_limit, phone=normalized_phone)
        return AdminOrdersPage.build(items=[self._to_read(order) for order in orders])

    async def update_order_status(self, *, order_id: int, status: str) -> OrderRead:
        order = await self.repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)

        next_status = status.strip()
        if next_status not in get_allowed_statuses(order.checkout_type):
            raise OrderValidationError("Некорректный статус для этого типа заказа.")

        updated_order = await self.repository.update_status(order_id=order_id, status=next_status)
        if updated_order is None:
            raise OrderNotFoundError(order_id)

        return self._to_read(updated_order)

    def _to_read(self, order) -> OrderRead:
        return OrderRead(
            id=order.id,
            user_id=order.user_id,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            checkout_type=order.checkout_type,
            payment_type=order.payment_type,
            delivery_address=order.delivery_address,
            entrance=order.entrance,
            comment=order.comment,
            items=json.loads(order.items_json),
            items_count=order.items_count,
            cutlery_count=order.cutlery_count,
            subtotal_amount=order.subtotal_amount,
            bonus_spent=order.bonus_spent,
            total_amount=order.total_amount,
            bonus_awarded=order.bonus_awarded,
            iiko_order_id=order.iiko_order_id,
            iiko_correlation_id=order.iiko_correlation_id,
            iiko_creation_status=order.iiko_creation_status,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def _normalize_order_items(self, payload: OrderCreate) -> list[NormalizedOrderItem]:
        ordered_ids: list[int] = []
        quantities_by_id: dict[int, int] = {}
        for item in payload.items:
            try:
                item_id = int(item.id)
            except (TypeError, ValueError) as exc:
                raise OrderValidationError("Некорректный идентификатор позиции в заказе.") from exc
            if item_id not in quantities_by_id:
                ordered_ids.append(item_id)
                quantities_by_id[item_id] = 0
            quantities_by_id[item_id] += item.quantity

        menu_items = await self.menu_item_repository.get_many_by_ids(ordered_ids)
        menu_items_by_id = {item.id: item for item in menu_items}
        if len(menu_items_by_id) != len(ordered_ids):
            raise OrderValidationError("Одна или несколько позиций заказа больше недоступны.")

        normalized_items: list[NormalizedOrderItem] = []
        for item_id in ordered_ids:
            menu_item = menu_items_by_id[item_id]
            if not menu_item.is_active or not menu_item.is_published:
                raise OrderValidationError(f"Позиция «{menu_item.title}» сейчас недоступна для заказа.")
            if not menu_item.iiko_product_id:
                raise OrderValidationError(f"Позиция «{menu_item.title}» не связана с товаром iiko.")

            normalized_items.append(
                NormalizedOrderItem(
                    order_item=OrderItemPayload(
                        id=str(menu_item.id),
                        title=menu_item.site_title or menu_item.title,
                        price=int(menu_item.price),
                        quantity=quantities_by_id[item_id],
                    ),
                    iiko_product_id=str(menu_item.iiko_product_id),
                )
            )

        return normalized_items
