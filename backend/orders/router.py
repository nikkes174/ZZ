from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.auth.dependencies import require_admin_user, require_current_user
from backend.orders.depencises import get_order_service
from backend.orders.schemas import AdminOrdersPage, OrderCreate, OrderRead, OrderStatusUpdate, UserOrdersPage
from backend.orders.service import OrderNotFoundError, OrderService, OrderValidationError
from backend.payment.depencises import get_yookassa_payment_service
from backend.payment.schemas import PaymentInitRead
from backend.payment.service import PaymentError, YooKassaPaymentService
from backend.user.depencises import get_user_service
from backend.user.schemas import UserRead
from backend.user.service import UserService

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=PaymentInitRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    user: UserRead = Depends(require_current_user),
    order_service: OrderService = Depends(get_order_service),
    payment_service: YooKassaPaymentService = Depends(get_yookassa_payment_service),
    user_service: UserService = Depends(get_user_service),
) -> PaymentInitRead:
    try:
        prepared_order = await order_service.prepare_order(
            payload=payload,
            available_bonus_balance=user.bonus_balance,
        )
        if prepared_order.total_amount <= 0:
            order = await order_service.create_order(
                user_id=user.id,
                payload=prepared_order.payload,
                available_bonus_balance=user.bonus_balance,
            )
            updated_user = user
            bonus_delta = order.bonus_awarded - order.bonus_spent
            if bonus_delta:
                updated_user = await user_service.add_bonus(user_id=user.id, bonus_delta=bonus_delta)
            return PaymentInitRead(
                status="created",
                order_id=order.id,
                total_amount=order.total_amount,
                bonus_spent=order.bonus_spent,
                bonus_awarded=order.bonus_awarded,
                bonus_balance=updated_user.bonus_balance,
            )

        payment = await payment_service.create_payment(
            user_id=user.id,
            user_phone=user.phone,
            payload=prepared_order.payload,
            amount=prepared_order.total_amount,
        )
        payment.total_amount = prepared_order.total_amount
        payment.bonus_spent = prepared_order.payload.bonus_spent
        return payment
    except OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/my", response_model=UserOrdersPage)
async def list_my_orders(
    user: UserRead = Depends(require_current_user),
    order_service: OrderService = Depends(get_order_service),
) -> UserOrdersPage:
    return await order_service.list_user_orders(user.id)


@router.get("/admin", response_model=AdminOrdersPage)
async def list_admin_orders(
    limit: int = Query(default=30, ge=1, le=100),
    phone: Optional[str] = Query(default=None, min_length=6, max_length=32),
    admin_user: UserRead = Depends(require_admin_user),
    order_service: OrderService = Depends(get_order_service),
) -> AdminOrdersPage:
    _ = admin_user
    return await order_service.list_admin_orders(limit=limit, phone=phone)


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    admin_user: UserRead = Depends(require_admin_user),
    order_service: OrderService = Depends(get_order_service),
) -> OrderRead:
    _ = admin_user
    try:
        return await order_service.update_order_status(order_id=order_id, status=payload.status)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.") from exc
    except OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
