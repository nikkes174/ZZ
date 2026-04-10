from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from backend.orders.crud import OrderRepository
from backend.orders.schemas import AdminOrdersPage, OrderCreate, OrderRead, UserOrdersPage
from backend.orders.statuses import get_allowed_statuses


class OrderValidationError(Exception):
    pass


class OrderNotFoundError(Exception):
    pass


@dataclass
class OrderService:
    repository: OrderRepository

    async def create_order(self, *, user_id: int, payload: OrderCreate, available_bonus_balance: int) -> OrderRead:
        subtotal_amount = sum(item.price * item.quantity for item in payload.items)
        if subtotal_amount <= 0:
            raise OrderValidationError("Сумма заказа должна быть больше нуля.")
        if payload.checkout_type == "delivery" and not (payload.delivery_address or "").strip():
            raise OrderValidationError("Укажите адрес доставки.")
        if payload.bonus_spent > available_bonus_balance:
            raise OrderValidationError("Недостаточно бонусов для списания.")
        if payload.bonus_spent > subtotal_amount:
            raise OrderValidationError("Нельзя списать бонусов больше суммы заказа.")

        total_amount = subtotal_amount - payload.bonus_spent
        bonus_awarded = max(0, total_amount // 20)
        order = await self.repository.create(
            user_id=user_id,
            payload=payload,
            subtotal_amount=subtotal_amount,
            bonus_spent=payload.bonus_spent,
            total_amount=total_amount,
            bonus_awarded=bonus_awarded,
        )
        return self._to_read(order)

    async def list_user_orders(self, user_id: int) -> UserOrdersPage:
        orders = await self.repository.list_by_user(user_id)
        return UserOrdersPage(items=[self._to_read(order) for order in orders])

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
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
