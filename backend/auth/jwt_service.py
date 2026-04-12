from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from config import JWT_ACCESS_TOKEN_TTL_MINUTES, JWT_ALGORITHM, JWT_REFRESH_TOKEN_TTL_MINUTES, JWT_SECRET


class JWTError(Exception):
    pass


class JWTService:
    def create_access_token(self, *, user_id: int, is_admin: bool) -> tuple[str, int]:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=JWT_ACCESS_TOKEN_TTL_MINUTES)
        payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "is_admin": is_admin,
            "type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return self._encode(payload), int((exp - now).total_seconds())

    def create_refresh_token(self, *, user_id: int) -> tuple[str, str, datetime, int]:
        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=JWT_REFRESH_TOKEN_TTL_MINUTES)
        jti = str(uuid4())
        payload = {
            "sub": str(user_id),
            "user_id": user_id,
            "jti": jti,
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return self._encode(payload), jti, exp, int((exp - now).total_seconds())

    def decode_access_token(self, token: str) -> dict[str, object]:
        payload = self._decode(token)
        if payload.get("type") != "access" or not isinstance(payload.get("user_id"), int):
            raise JWTError("Invalid access token.")
        return payload

    def decode_refresh_token(self, token: str) -> dict[str, object]:
        payload = self._decode(token)
        if payload.get("type") != "refresh" or not isinstance(payload.get("user_id"), int):
            raise JWTError("Invalid refresh token.")
        if not isinstance(payload.get("jti"), str) or not payload.get("jti"):
            raise JWTError("Invalid refresh token.")
        return payload

    def _encode(self, payload: dict[str, object]) -> str:
        if not JWT_SECRET:
            raise JWTError("JWT_SECRET is not configured.")
        header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
        signing_input = f"{self._b64_json(header)}.{self._b64_json(payload)}"
        signature = hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{self._b64(signature)}"

    def _decode(self, token: str) -> dict[str, object]:
        if not JWT_SECRET:
            raise JWTError("JWT_SECRET is not configured.")
        try:
            header_raw, payload_raw, signature_raw = token.split(".", 2)
        except ValueError as exc:
            raise JWTError("Invalid token.") from exc

        header = self._loads(header_raw)
        if header.get("alg") != JWT_ALGORITHM:
            raise JWTError("Invalid token algorithm.")

        signing_input = f"{header_raw}.{payload_raw}"
        expected = self._b64(
            hmac.new(JWT_SECRET.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(expected, signature_raw):
            raise JWTError("Invalid token signature.")

        payload = self._loads(payload_raw)
        exp = payload.get("exp")
        if not isinstance(exp, int) or exp <= int(datetime.now(timezone.utc).timestamp()):
            raise JWTError("Token expired.")
        return payload

    def _loads(self, value: str) -> dict[str, object]:
        try:
            decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
            payload = json.loads(decoded)
        except (ValueError, json.JSONDecodeError) as exc:
            raise JWTError("Invalid token payload.") from exc
        if not isinstance(payload, dict):
            raise JWTError("Invalid token payload.")
        return payload

    def _b64_json(self, value: dict[str, object]) -> str:
        return self._b64(json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))

    def _b64(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
