from __future__ import annotations

import logging
from dataclasses import dataclass

from backend.auth.email_sender import SMTPEmailSender
from backend.auth.reset_tokens_repo import DatabaseResetTokenRepository
from backend.user.crud import SqlAlchemyUserRepository
from backend.user.service import UserAuthError, UserService


logger = logging.getLogger(__name__)


class PasswordResetError(Exception):
    pass


@dataclass
class PasswordRecoveryService:
    user_repository: SqlAlchemyUserRepository
    token_repository: DatabaseResetTokenRepository
    email_sender: SMTPEmailSender

    def _normalize_email(self, email: str) -> str:
        return UserService(self.user_repository).normalize_email(email)

    async def request_recovery(self, *, email: str) -> None:
        normalized_email = self._normalize_email(email)
        user = await self.user_repository.get_by_email(normalized_email)
        if user is None:
            logger.info("Password recovery requested for unknown email.")
            return

        token = await self.token_repository.create(user_id=user.id)
        text = (
            "Восстановление пароля Zamzam\n\n"
            f"Код восстановления:\n{token}\n\n"
            "Срок действия: 10 минут."
        )
        await self.email_sender.send(
            email=normalized_email,
            subject="Восстановление пароля Zamzam",
            text=text,
        )

    async def confirm_recovery(self, *, token: str, password: str) -> None:
        user_id = await self.token_repository.consume(token=token.strip())
        if user_id is None:
            raise PasswordResetError("Неверный или просроченный код восстановления.")

        try:
            await UserService(self.user_repository).reset_password(user_id=user_id, password=password)
        except UserAuthError as exc:
            raise PasswordResetError(str(exc)) from exc
