from __future__ import annotations

import hashlib
import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from backend.auth.dependencies import require_admin_user, require_current_user
from backend.orders.availability import ensure_order_time_open
from backend.orders.depencises import get_order_service
from backend.orders.schemas import AdminOrdersPage, OrderCreate, OrderRead, OrderStatusUpdate, UserOrdersPage
from backend.orders.service import OrderNotFoundError, OrderService, OrderValidationError
from backend.payment.depencises import get_yookassa_payment_service
from backend.payment.schemas import PaymentInitRead
from backend.payment.service import PaymentError, YooKassaPaymentService
from backend.rate_limit import client_ip, rate_limiter
from backend.user.depencises import get_user_service
from backend.user.schemas import UserRead
from backend.user.service import UserBonusError, UserService

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _build_order_idempotency_key(*, request: Request, user_id: int, payload: OrderCreate) -> str:
    header_key = (request.headers.get("idempotency-key") or "").strip()
    if header_key:
        return f"client:{user_id}:{header_key[:96]}"

    bucket = int(time.time() // 300)
    raw = json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"auto:{user_id}:{bucket}:{digest}"


@router.post("", response_model=PaymentInitRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    request: Request,
    user: UserRead = Depends(require_current_user),
    order_service: OrderService = Depends(get_order_service),
    payment_service: YooKassaPaymentService = Depends(get_yookassa_payment_service),
    user_service: UserService = Depends(get_user_service),
) -> PaymentInitRead:
    ensure_order_time_open()
    await rate_limiter.check(key=f"orders-create:ip:{client_ip(request)}", limit=30, window_seconds=60)
    await rate_limiter.check(key=f"orders-create:user:{user.id}", limit=10, window_seconds=60)
    try:
        prepared_order = await order_service.prepare_order(
            payload=payload,
            available_bonus_balance=user.bonus_balance,
        )
        if prepared_order.total_amount <= 0:
            idempotency_key = _build_order_idempotency_key(
                request=request,
                user_id=user.id,
                payload=prepared_order.payload,
            )
            existing_order = await order_service.get_by_idempotency_key(idempotency_key)
            if existing_order is not None:
                existing_status = "created"
                if existing_order.iiko_creation_status == "LocalPending":
                    existing_status = "processing"
                elif existing_order.iiko_creation_status == "Failed":
                    existing_status = "failed"
                return PaymentInitRead(
                    status=existing_status,
                    order_id=existing_order.id,
                    total_amount=existing_order.total_amount,
                    bonus_spent=existing_order.bonus_spent,
                    bonus_awarded=existing_order.bonus_awarded,
                    bonus_balance=user.bonus_balance,
                )

            claimed_order = await order_service.claim_order_creation(
                user_id=user.id,
                payload=prepared_order.payload,
                available_bonus_balance=user.bonus_balance,
                idempotency_key=idempotency_key,
            )
            if not claimed_order.is_owner or claimed_order.prepared_order is None:
                existing_order = claimed_order.order
                existing_status = "created"
                if existing_order.iiko_creation_status == "LocalPending":
                    existing_status = "processing"
                elif existing_order.iiko_creation_status == "Failed":
                    existing_status = "failed"
                return PaymentInitRead(
                    status=existing_status,
                    order_id=existing_order.id,
                    total_amount=existing_order.total_amount,
                    bonus_spent=existing_order.bonus_spent,
                    bonus_awarded=existing_order.bonus_awarded,
                    bonus_balance=user.bonus_balance,
                )

            updated_user = user
            spent_bonus = prepared_order.payload.bonus_spent
            if spent_bonus:
                updated_user = await user_service.spend_bonus(user_id=user.id, bonus_amount=spent_bonus)
            try:
                order = await order_service.submit_claimed_order(
                    order_id=claimed_order.order.id,
                    prepared_order=claimed_order.prepared_order,
                )
            except Exception:
                if spent_bonus:
                    await user_service.refund_bonus(user_id=user.id, bonus_amount=spent_bonus)
                raise
            if order.bonus_awarded:
                updated_user = await user_service.add_bonus(user_id=user.id, bonus_delta=order.bonus_awarded)
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
    except UserBonusError as exc:
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
