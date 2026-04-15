from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.schemas import AuthTokenRead, RefreshTokenRequest
from backend.auth.token_service import AuthTokenError, AuthTokenService
from backend.rate_limit import client_ip, rate_limiter
from backend.user.depencises import get_user_service
from backend.user.schemas import UserLoginRequest, UserRegisterRequest
from backend.user.service import UserAuthError, UserService
from db import get_db


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
token_service = AuthTokenService()


@router.post("/register", response_model=AuthTokenRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_db),
) -> AuthTokenRead:
    logger.info("HTTP register request received.")
    await rate_limiter.check(key=f"auth-register:ip:{client_ip(request)}", limit=10, window_seconds=3600)
    await rate_limiter.check(key=f"auth-register:phone:{payload.phone.strip()}", limit=3, window_seconds=3600)
    try:
        auth_result = await service.register(payload)
        return await token_service.issue_token_pair(session=session, user=auth_result.user)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=AuthTokenRead)
async def login_user(
    payload: UserLoginRequest,
    request: Request,
    service: UserService = Depends(get_user_service),
    session: AsyncSession = Depends(get_db),
) -> AuthTokenRead:
    logger.info("HTTP login request received.")
    await rate_limiter.check(key=f"auth-login:ip:{client_ip(request)}", limit=30, window_seconds=60)
    await rate_limiter.check(key=f"auth-login:phone:{payload.phone.strip()}", limit=10, window_seconds=600)
    try:
        auth_result = await service.login(payload)
        return await token_service.issue_token_pair(session=session, user=auth_result.user)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/refresh", response_model=AuthTokenRead)
async def refresh_token(
    payload: RefreshTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> AuthTokenRead:
    await rate_limiter.check(key=f"auth-refresh:ip:{client_ip(request)}", limit=60, window_seconds=60)
    try:
        return await token_service.refresh_token_pair(session=session, refresh_token=payload.refresh_token)
    except AuthTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/logout")
async def logout_user(
    payload: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    logger.info("HTTP logout request received.")
    try:
        await token_service.revoke_refresh_token(session=session, refresh_token=payload.refresh_token)
    except AuthTokenError:
        pass
    return {"ok": True}
