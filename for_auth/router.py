from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import DEBUG
from backend.db import get_db
from backend.exceptions import ForbiddenError

from .auth_service import AuthService
from .schemas import AuthTokenResponse, DevAdminAuthRequest, DevUserAuthRequest, RefreshTokenRequest

router = APIRouter(prefix="/auth", tags=["Auth"])
service = AuthService()


@router.post(
    "/telegram",
    response_model=AuthTokenResponse,
    summary="Авторизация через Telegram MiniApp",
)
async def auth_telegram(
    init_data: str = Header(..., alias="init-data"),
    db: AsyncSession = Depends(get_db),
):
    user = await service.auth_telegram_user(db, init_data)
    return await service.issue_token_pair(db, user)


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    summary="Обновить access token по refresh token",
)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    return await service.refresh_token_pair(db, data.refresh_token)


@router.post(
    "/logout",
    summary="Выйти из сессии (отозвать refresh token)",
)
async def logout(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    await service.revoke_refresh_token(db, data.refresh_token)
    return {"ok": True}


@router.post(
    "/dev-admin",
    response_model=AuthTokenResponse,
    summary="DEV: получить токены админа по tg_id",
)
async def dev_admin_auth(
    data: DevAdminAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    if not DEBUG:
        raise ForbiddenError("DEV auth route is disabled")
    return await service.issue_dev_admin_token_pair(db, data.tg_id)


@router.post(
    "/dev-user",
    response_model=AuthTokenResponse,
    summary="DEV: получить токены обычного пользователя по tg_id",
)
async def dev_user_auth(
    data: DevUserAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    if not DEBUG:
        raise ForbiddenError("DEV auth route is disabled")
    return await service.issue_dev_user_token_pair(db, data.tg_id)
