import logging

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.exceptions import ForbiddenError, InvalidAccessTokenError, MissingAccessTokenError
from backend.user.models import User

from .auth_service import AuthService
from .jwt_service import JWTService

jwt_service = JWTService()
auth_service = AuthService()
logger = logging.getLogger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    init_data = request.headers.get("init-data") if request else None
    logger.info(
        "auth headers bearer=%s init_data_len=%s",
        bool(credentials and credentials.credentials),
        len(init_data) if init_data else 0,
    )
    if credentials and credentials.credentials:
        payload = jwt_service.decode_access_token(credentials.credentials)
        tg_id = int(payload["tg_id"])

        result = await db.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            raise InvalidAccessTokenError()
        return user

    # Temporary fallback for Swagger/manual testing without Bearer token.
    if init_data:
        return await auth_service.auth_telegram_user(db, init_data)

    raise MissingAccessTokenError()


async def get_admin_user(user=Depends(get_current_user)):
    if not getattr(user, "is_admin", False):
        logger.warning("Forbidden admin access for tg_id=%s", getattr(user, "tg_id", None))
        raise ForbiddenError("Нет прав")
    return user


async def get_buyer_user(user=Depends(get_current_user)):
    if getattr(user, "is_admin", False):
        logger.warning("Buyer route denied for admin tg_id=%s", getattr(user, "tg_id", None))
        raise ForbiddenError("Доступно только пользователю")
    return user
