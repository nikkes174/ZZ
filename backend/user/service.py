from __future__ import annotations

import hashlib
import hmac
import logging
import re
from dataclasses import dataclass
from secrets import token_hex
from typing import Optional

from backend.user.crud import UserRepository
from backend.user.migrations import is_admin_phone
from backend.user.schemas import UserAuthRead, UserDashboardRead, UserLoginRequest, UserRead, UserRegisterRequest


logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class UserAuthError(Exception):
    pass


class UserConflictError(Exception):
    pass


@dataclass
class UserService:
    repository: UserRepository

    def normalize_phone(self, phone: str) -> str:
        digits = re.sub(r"\D+", "", phone)
        if len(digits) == 11 and digits.startswith("8"):
            digits = f"7{digits[1:]}"
        if len(digits) != 11 or not digits.startswith("7"):
            raise UserAuthError("Укажите корректный номер телефона в формате +7.")
        return f"+{digits}"

    def _hash_password(self, password: str) -> str:
        normalized = password.strip()
        if len(normalized) < 6:
            raise UserAuthError("Пароль должен содержать не менее 6 символов.")

        salt = token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            normalized.encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        )
        return f"{salt}${digest.hex()}"

    def _verify_password(self, password: str, password_hash: Optional[str]) -> bool:
        if not password_hash:
            return False
        try:
            salt, digest = password_hash.split("$", 1)
        except ValueError:
            return False

        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.strip().encode("utf-8"),
            salt.encode("utf-8"),
            120_000,
        ).hex()
        return hmac.compare_digest(candidate, digest)

    async def register(self, payload: UserRegisterRequest) -> UserAuthRead:
        normalized_phone = self.normalize_phone(payload.phone)
        full_name = (payload.full_name or "").strip() or None
        password_hash = self._hash_password(payload.password)
        session_token = token_hex(24)
        is_admin = is_admin_phone(normalized_phone)
        logger.info("Registering user. phone=%s", normalized_phone)

        user = await self.repository.get_by_phone(normalized_phone)
        if user is not None and user.password_hash:
            raise UserAuthError("Пользователь с таким номером уже зарегистрирован.")

        if user is None:
            created_user = await self.repository.create_user(
                phone=normalized_phone,
                password_hash=password_hash,
                full_name=full_name,
                session_token=session_token,
                is_admin=is_admin,
            )
        else:
            created_user = await self.repository.activate_existing_user(
                user_id=user.id,
                password_hash=password_hash,
                full_name=full_name,
                session_token=session_token,
                is_admin=is_admin,
            )

        return UserAuthRead(
            session_token=session_token,
            user=UserRead.model_validate(created_user),
        )

    async def login(self, payload: UserLoginRequest) -> UserAuthRead:
        normalized_phone = self.normalize_phone(payload.phone)
        logger.info("Login attempt. phone=%s", normalized_phone)
        user = await self.repository.get_by_phone(normalized_phone)
        if user is None or not self._verify_password(payload.password, user.password_hash):
            logger.warning("Login failed. phone=%s", normalized_phone)
            raise UserAuthError("Неверный номер телефона или пароль.")

        session_token = token_hex(24)
        logged_user = await self.repository.update_session_token(
            user_id=user.id,
            session_token=session_token,
            is_admin=is_admin_phone(normalized_phone),
        )
        logger.info("Login succeeded. user_id=%s", logged_user.id)
        return UserAuthRead(
            session_token=session_token,
            user=UserRead.model_validate(logged_user),
        )

    async def logout(self, *, session_token: str) -> UserRead:
        user = await self.repository.get_by_session_token(session_token)
        if user is None:
            raise UserNotFoundError(session_token)

        logged_out_user = await self.repository.clear_session_token(user_id=user.id)
        if logged_out_user is None:
            raise UserNotFoundError(session_token)

        logger.info("Logout succeeded. user_id=%s", logged_out_user.id)
        return UserRead.model_validate(logged_out_user)

    async def get_user_by_session_token(self, session_token: str) -> UserRead:
        user = await self.repository.get_by_session_token(session_token)
        if user is None:
            raise UserNotFoundError(session_token)
        return UserRead.model_validate(user)

    async def get_user_by_id(self, user_id: int) -> UserRead:
        user = await self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        env_admin = is_admin_phone(user.phone)
        if user.is_admin != env_admin:
            user = await self.repository.update_admin_status(user_id=user.id, is_admin=env_admin)
        return UserRead.model_validate(user)

    async def add_bonus(self, *, user_id: int, bonus_delta: int) -> UserRead:
        user = await self.repository.add_bonus(user_id=user_id, bonus_delta=bonus_delta)
        if user is None:
            raise UserNotFoundError(user_id)
        return UserRead.model_validate(user)

    async def update_phone(self, *, user_id: int, phone: str) -> UserRead:
        normalized_phone = self.normalize_phone(phone)
        existing_user = await self.repository.get_by_phone(normalized_phone)
        if existing_user is not None and existing_user.id != user_id:
            raise UserConflictError("Этот номер телефона уже используется.")

        user = await self.repository.update_phone(
            user_id=user_id,
            phone=normalized_phone,
            is_admin=is_admin_phone(normalized_phone),
        )
        return UserRead.model_validate(user)

    def build_dashboard(
        self,
        *,
        user: UserRead,
        latest_order_status: Optional[str],
        active_orders_count: int,
    ) -> UserDashboardRead:
        return UserDashboardRead(
            user=user,
            latest_order_status=latest_order_status,
            active_orders_count=active_orders_count,
        )
