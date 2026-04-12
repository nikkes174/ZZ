from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.auth.dependencies import require_current_user
from backend.orders.depencises import get_order_service
from backend.orders.service import OrderService
from backend.user.depencises import get_user_service
from backend.user.schemas import UserDashboardRead, UserProfileUpdateRequest, UserRead
from backend.user.service import UserAuthError, UserConflictError, UserService

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/me", response_model=UserDashboardRead)
async def get_current_user_dashboard(
    user: UserRead = Depends(require_current_user),
    user_service: UserService = Depends(get_user_service),
    order_service: OrderService = Depends(get_order_service),
) -> UserDashboardRead:
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
    user: UserRead = Depends(require_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        return await user_service.update_phone(user_id=user.id, phone=payload.phone)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UserConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
