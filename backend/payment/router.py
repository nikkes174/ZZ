from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from backend.auth.dependencies import require_current_user
from backend.orders.depencises import get_order_service
from backend.orders.schemas import OrderCreate
from backend.orders.service import OrderService, OrderValidationError
from backend.payment.depencises import get_pending_payment_repository, get_yookassa_payment_service
from backend.payment.crud import SqlAlchemyPendingPaymentRepository
from backend.payment.service import PaymentError, YooKassaPaymentService
from backend.user.depencises import get_user_service
from backend.user.schemas import UserRead
from backend.user.service import UserNotFoundError, UserService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])


async def _finalize_succeeded_payment(
    *,
    payment_id: str,
    payment_service: YooKassaPaymentService,
    pending_payment_repository: SqlAlchemyPendingPaymentRepository,
    order_service: OrderService,
    user_service: UserService,
) -> dict[str, object]:
    try:
        payment_payload = await payment_service.fetch_payment(payment_id)
    except PaymentError:
        logger.exception("Could not verify YooKassa payment. payment_id=%s", payment_id)
        raise

    if str(payment_payload.get("status") or "") != "succeeded":
        return {"ok": True, "status": str(payment_payload.get("status") or "")}

    pending_payment = await pending_payment_repository.get_by_yookassa_payment_id(payment_id)
    if pending_payment is None:
        logger.warning("YooKassa webhook payment was not found locally. payment_id=%s", payment_id)
        return {"ok": True}
    if pending_payment.order_id is not None:
        return {"ok": True, "order_id": pending_payment.order_id}

    try:
        order_payload = OrderCreate.model_validate(json.loads(pending_payment.payload_json))
        user = await user_service.get_user_by_id(pending_payment.user_id)
        order = await order_service.create_order(
            user_id=pending_payment.user_id,
            payload=order_payload,
            available_bonus_balance=user.bonus_balance,
        )
        bonus_delta = order.bonus_awarded - order.bonus_spent
        if bonus_delta:
            await user_service.add_bonus(user_id=pending_payment.user_id, bonus_delta=bonus_delta)
        await pending_payment_repository.mark_order_created(
            pending_payment_id=pending_payment.id,
            order_id=order.id,
        )
        return {"ok": True, "order_id": order.id}
    except (OrderValidationError, UserNotFoundError) as exc:
        logger.exception("Could not create order after YooKassa payment. payment_id=%s", payment_id)
        await pending_payment_repository.mark_failed(
            pending_payment_id=pending_payment.id,
            status="order_failed",
            error_message=str(exc),
        )
        raise


@router.post("/yookassa/webhook")
async def yookassa_webhook(
    request: Request,
    payment_service: YooKassaPaymentService = Depends(get_yookassa_payment_service),
    pending_payment_repository: SqlAlchemyPendingPaymentRepository = Depends(get_pending_payment_repository),
    order_service: OrderService = Depends(get_order_service),
    user_service: UserService = Depends(get_user_service),
) -> JSONResponse:
    payload: dict[str, Any] = await request.json()
    event = str(payload.get("event") or "")
    payment_object = payload.get("object") or {}
    payment_id = str(payment_object.get("id") or "")
    payment_status = str(payment_object.get("status") or "")
    if event and event != "payment.succeeded":
        return JSONResponse({"ok": True})
    if not payment_id or payment_status != "succeeded":
        return JSONResponse({"ok": True})

    try:
        result = await _finalize_succeeded_payment(
            payment_id=payment_id,
            payment_service=payment_service,
            pending_payment_repository=pending_payment_repository,
            order_service=order_service,
            user_service=user_service,
        )
    except (PaymentError, OrderValidationError, UserNotFoundError):
        return JSONResponse({"ok": False}, status_code=400)
    return JSONResponse(result)


@router.post("/{payment_id}/sync")
async def sync_payment(
    payment_id: str,
    user: UserRead = Depends(require_current_user),
    payment_service: YooKassaPaymentService = Depends(get_yookassa_payment_service),
    pending_payment_repository: SqlAlchemyPendingPaymentRepository = Depends(get_pending_payment_repository),
    order_service: OrderService = Depends(get_order_service),
    user_service: UserService = Depends(get_user_service),
) -> JSONResponse:
    pending_payment = await pending_payment_repository.get_by_yookassa_payment_id(payment_id)
    if pending_payment is None or pending_payment.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found.")

    try:
        result = await _finalize_succeeded_payment(
            payment_id=payment_id,
            payment_service=payment_service,
            pending_payment_repository=pending_payment_repository,
            order_service=order_service,
            user_service=user_service,
        )
    except PaymentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except (OrderValidationError, UserNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return JSONResponse(result)
