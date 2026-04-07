from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.orders.depencises import get_order_service
from backend.orders.schemas import OrderCreate, OrderRead, UserOrdersPage
from backend.orders.service import OrderService, OrderValidationError
from backend.user.depencises import get_session_token, get_user_service
from backend.user.service import UserNotFoundError, UserService

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    session_token: str = Depends(get_session_token),
    order_service: OrderService = Depends(get_order_service),
    user_service: UserService = Depends(get_user_service),
) -> OrderRead:
    try:
        user = await user_service.get_user_by_session_token(session_token)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия не найдена.") from exc

    try:
        order = await order_service.create_order(
            user_id=user.id,
            payload=payload,
            available_bonus_balance=user.bonus_balance,
        )
    except OrderValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    bonus_delta = order.bonus_awarded - order.bonus_spent
    if bonus_delta:
        await user_service.add_bonus(user_id=user.id, bonus_delta=bonus_delta)
    return order


@router.get("/my", response_model=UserOrdersPage)
async def list_my_orders(
    session_token: str = Depends(get_session_token),
    order_service: OrderService = Depends(get_order_service),
    user_service: UserService = Depends(get_user_service),
) -> UserOrdersPage:
    try:
        user = await user_service.get_user_by_session_token(session_token)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия не найдена.") from exc

    return await order_service.list_user_orders(user.id)
