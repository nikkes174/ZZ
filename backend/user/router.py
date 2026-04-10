from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.orders.depencises import get_order_service
from backend.orders.service import OrderService
from backend.user.depencises import get_session_token, get_user_service
from backend.user.schemas import UserAuthRead, UserDashboardRead, UserLoginRequest, UserProfileUpdateRequest, UserRead, UserRegisterRequest
from backend.user.service import UserAuthError, UserConflictError, UserNotFoundError, UserService

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/auth/register", response_model=UserAuthRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    service: UserService = Depends(get_user_service),
) -> UserAuthRead:
    try:
        return await service.register(payload)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/auth/login", response_model=UserAuthRead)
async def login_user(
    payload: UserLoginRequest,
    service: UserService = Depends(get_user_service),
) -> UserAuthRead:
    try:
        return await service.login(payload)
    except UserAuthError as exc:
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


@router.patch("/me", response_model=UserRead)
async def update_current_user(
    payload: UserProfileUpdateRequest,
    session_token: str = Depends(get_session_token),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await user_service.get_user_by_session_token(session_token)
        return await user_service.update_phone(user_id=user.id, phone=payload.phone)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия не найдена.") from exc
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
