from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from jwt import InvalidTokenError

from backend.config import (
    JWT_ACCESS_TOKEN_TTL_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_TOKEN_TTL_MINUTES,
    JWT_SECRET,
)
from backend.exceptions import InvalidAccessTokenError, InvalidRefreshTokenError


class JWTService:
    def create_access_token(self, tg_id: int, is_admin: bool) -> tuple[str, int]:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=JWT_ACCESS_TOKEN_TTL_MINUTES)

        payload = {
            "sub": str(tg_id),
            "tg_id": tg_id,
            "is_admin": is_admin,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        expires_in = int((exp - now).total_seconds())
        return token, expires_in

    def create_refresh_token(self, tg_id: int) -> tuple[str, str, datetime, int]:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=JWT_REFRESH_TOKEN_TTL_MINUTES)
        jti = str(uuid4())

        payload = {
            "sub": str(tg_id),
            "tg_id": tg_id,
            "jti": jti,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        expires_in = int((exp - now).total_seconds())
        return token, jti, exp, expires_in

    def decode_access_token(self, token: str) -> dict:
        payload = self._decode(token, InvalidAccessTokenError)
        if payload.get("type") != "access":
            raise InvalidAccessTokenError()

        tg_id = payload.get("tg_id")
        if not isinstance(tg_id, int):
            raise InvalidAccessTokenError()

        return payload

    def decode_refresh_token(self, token: str) -> dict:
        payload = self._decode(token, InvalidRefreshTokenError)
        if payload.get("type") != "refresh":
            raise InvalidRefreshTokenError()

        tg_id = payload.get("tg_id")
        jti = payload.get("jti")
        if not isinstance(tg_id, int) or not isinstance(jti, str) or not jti:
            raise InvalidRefreshTokenError()

        return payload

    def _decode(self, token: str, exc_type):
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except InvalidTokenError as exc:
            raise exc_type() from exc
