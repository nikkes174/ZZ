from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.jwt_service import JWTError, JWTService
from backend.user.depencises import get_user_service
from backend.user.schemas import UserRead
from backend.user.service import UserNotFoundError, UserService


bearer_scheme = HTTPBearer(auto_error=False)
jwt_service = JWTService()


async def require_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token is required.")
    try:
        payload = jwt_service.decode_access_token(credentials.credentials)
        return await user_service.get_user_by_id(int(payload["user_id"]))
    except (JWTError, UserNotFoundError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.") from exc


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    user_service: UserService = Depends(get_user_service),
) -> Optional[UserRead]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = jwt_service.decode_access_token(credentials.credentials)
        return await user_service.get_user_by_id(int(payload["user_id"]))
    except (JWTError, UserNotFoundError, KeyError, TypeError, ValueError):
        return None


async def require_admin_user(
    user: UserRead = Depends(require_current_user),
) -> UserRead:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user


def ensure_admin_user(user: Optional[UserRead]) -> UserRead:
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token is required.")
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required.")
    return user
