from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from secrets import randbelow, token_hex

from backend.user.crud import UserRepository
from backend.user.schemas import (
    AuthCodeResponse,
    AuthVerifyRequest,
    UserAuthRead,
    UserDashboardRead,
    UserRead,
)


class UserNotFoundError(Exception):
    pass


class VerificationCodeError(Exception):
    pass


@dataclass
class UserService:
    repository: UserRepository

    def normalize_phone(self, phone: str) -> str:
        digits = re.sub(r"\D+", "", phone)
        if len(digits) == 11 and digits.startswith("8"):
            digits = f"7{digits[1:]}"
        if len(digits) != 11 or not digits.startswith("7"):
            raise VerificationCodeError("Укажите корректный номер телефона в формате +7.")
        return f"+{digits}"

    async def request_code(self, phone: str) -> AuthCodeResponse:
        normalized_phone = self.normalize_phone(phone)
        code = f"{randbelow(9000) + 1000}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        await self.repository.create_or_update_code(
            phone=normalized_phone,
            code=code,
            expires_at=expires_at,
        )
        return AuthCodeResponse(
            phone=normalized_phone,
            message=f"Код подтверждения отправлен на номер {normalized_phone}.",
            code=code,
            expires_at=expires_at,
        )

    async def verify_code(self, payload: AuthVerifyRequest) -> UserAuthRead:
        normalized_phone = self.normalize_phone(payload.phone)
        user = await self.repository.get_by_phone(normalized_phone)
        if user is None:
            raise UserNotFoundError(normalized_phone)

        if (
            not user.verification_code
            or user.verification_code != payload.code.strip()
            or user.verification_expires_at is None
            or user.verification_expires_at < datetime.now(timezone.utc)
        ):
            raise VerificationCodeError("Код подтверждения недействителен или истек.")

        session_token = token_hex(24)
        verified_user = await self.repository.verify_user(
            user_id=user.id,
            full_name=(payload.full_name or "").strip() or None,
            session_token=session_token,
        )
        return UserAuthRead(
            session_token=session_token,
            user=UserRead.model_validate(verified_user),
        )

    async def get_user_by_session_token(self, session_token: str) -> UserRead:
        user = await self.repository.get_by_session_token(session_token)
        if user is None:
            raise UserNotFoundError(session_token)
        return UserRead.model_validate(user)

    async def add_bonus(self, *, user_id: int, bonus_delta: int) -> UserRead:
        user = await self.repository.add_bonus(user_id=user_id, bonus_delta=bonus_delta)
        if user is None:
            raise UserNotFoundError(user_id)
        return UserRead.model_validate(user)

    def build_dashboard(
        self,
        *,
        user: UserRead,
        latest_order_status: str | None,
        active_orders_count: int,
    ) -> UserDashboardRead:
        return UserDashboardRead(
            user=user,
            latest_order_status=latest_order_status,
            active_orders_count=active_orders_count,
        )
