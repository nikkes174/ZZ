from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.email_sender import EmailDeliveryError, SMTPEmailSender
from backend.auth.recovery_service import PasswordRecoveryService, PasswordResetError
from backend.auth.reset_tokens_repo import DatabaseResetTokenRepository
from backend.auth.schemas import AuthTokenRead, PasswordRecoveryRequest, PasswordResetRequest, RefreshTokenRequest
from backend.auth.token_service import AuthTokenError, AuthTokenService
from backend.rate_limit import client_ip, rate_limiter
from backend.user.crud import SqlAlchemyUserRepository
from backend.user.depencises import get_user_service
from backend.user.schemas import UserLoginRequest, UserRegisterRequest
from backend.user.service import UserAuthError, UserService
from config import SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USE_TLS, SMTP_USER
from db import get_db


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])
token_service = AuthTokenService()


def get_password_recovery_service(session: AsyncSession = Depends(get_db)) -> PasswordRecoveryService:
    return PasswordRecoveryService(
        user_repository=SqlAlchemyUserRepository(session),
        token_repository=DatabaseResetTokenRepository(session),
        email_sender=SMTPEmailSender(
            host=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            from_email=SMTP_FROM,
            use_tls=SMTP_USE_TLS,
        ),
    )


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
    await rate_limiter.check(key=f"auth-register:email:{payload.email.strip().lower()}", limit=3, window_seconds=3600)
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


@router.post("/password/recovery")
async def request_password_recovery(
    payload: PasswordRecoveryRequest,
    request: Request,
    service: PasswordRecoveryService = Depends(get_password_recovery_service),
) -> dict[str, bool]:
    await rate_limiter.check(key=f"auth-recovery:ip:{client_ip(request)}", limit=5, window_seconds=3600)
    await rate_limiter.check(key=f"auth-recovery:email:{payload.email.strip().lower()}", limit=3, window_seconds=3600)
    try:
        await service.request_recovery(email=payload.email)
    except UserAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except EmailDeliveryError as exc:
        logger.warning(
            "Password recovery email delivery failed. reason=%s detail=%s",
            type(exc.__cause__).__name__ if exc.__cause__ else type(exc).__name__,
            str(exc.__cause__ or exc),
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Не удалось отправить письмо.") from exc
    return {"ok": True}


@router.post("/password/reset")
async def reset_password(
    payload: PasswordResetRequest,
    request: Request,
    service: PasswordRecoveryService = Depends(get_password_recovery_service),
) -> dict[str, bool]:
    await rate_limiter.check(key=f"auth-reset:ip:{client_ip(request)}", limit=10, window_seconds=3600)
    try:
        await service.confirm_recovery(token=payload.token, password=payload.password)
    except PasswordResetError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {"ok": True}


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
