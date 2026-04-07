from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.orders.depencises import get_order_service
from backend.orders.service import OrderService
from backend.user.depencises import get_session_token, get_user_service
from backend.user.schemas import (
    AuthCodeRequest,
    AuthCodeResponse,
    AuthVerifyRequest,
    UserAuthRead,
    UserDashboardRead,
)
from backend.user.service import UserNotFoundError, UserService, VerificationCodeError

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/auth/request-code", response_model=AuthCodeResponse)
async def request_auth_code(
    payload: AuthCodeRequest,
    service: UserService = Depends(get_user_service),
) -> AuthCodeResponse:
    try:
        return await service.request_code(payload.phone)
    except VerificationCodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/auth/verify", response_model=UserAuthRead)
async def verify_auth_code(
    payload: AuthVerifyRequest,
    service: UserService = Depends(get_user_service),
) -> UserAuthRead:
    try:
        return await service.verify_code(payload)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден.") from exc
    except VerificationCodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/me", response_model=UserDashboardRead)
async def get_current_user_dashboard(
    session_token: str = Depends(get_session_token),
    user_service: UserService = Depends(get_user_service),
    order_service: OrderService = Depends(get_order_service),
) -> UserDashboardRead:
    try:
        user = await user_service.get_user_by_session_token(session_token)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия не найдена.") from exc

    latest_order_status = await order_service.get_latest_status(user.id)
    active_orders_count = await order_service.count_active_orders(user.id)
    return user_service.build_dashboard(
        user=user,
        latest_order_status=latest_order_status,
        active_orders_count=active_orders_count,
    )
