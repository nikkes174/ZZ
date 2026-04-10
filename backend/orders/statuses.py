from __future__ import annotations

ORDER_STATUS_PREPARING = "Готовится"
ORDER_STATUS_DELIVERY_SENT = "Заказ отправлен"
ORDER_STATUS_DELIVERED = "Доставлен"
ORDER_STATUS_PICKUP_READY = "Готов к выдаче"
ORDER_STATUS_PICKUP_DONE = "Выдан"
ORDER_STATUS_CANCELLED = "Отменен"

ORDER_STATUSES_BY_CHECKOUT_TYPE: dict[str, tuple[str, ...]] = {
    "delivery": (
        ORDER_STATUS_PREPARING,
        ORDER_STATUS_DELIVERY_SENT,
        ORDER_STATUS_DELIVERED,
        ORDER_STATUS_CANCELLED,
    ),
    "pickup": (
        ORDER_STATUS_PREPARING,
        ORDER_STATUS_PICKUP_READY,
        ORDER_STATUS_PICKUP_DONE,
        ORDER_STATUS_CANCELLED,
    ),
}

ACTIVE_ORDER_STATUSES = {
    ORDER_STATUS_PREPARING,
    ORDER_STATUS_DELIVERY_SENT,
    ORDER_STATUS_PICKUP_READY,
}


def get_allowed_statuses(checkout_type: str) -> tuple[str, ...]:
    return ORDER_STATUSES_BY_CHECKOUT_TYPE.get(checkout_type, (ORDER_STATUS_PREPARING,))
