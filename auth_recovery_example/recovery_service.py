from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth_recovery.email_sender import SMTPEmailSender
from backend.auth_recovery.passwords import PasswordHasher
from backend.auth_recovery.reset_tokens_repo import ResetTokenRepository
from backend.User.models import UserModel


class PasswordRecoveryService:
    def __init__(
        self,
        session: AsyncSession,
        token_repo: ResetTokenRepository,
        email_sender: SMTPEmailSender,
    ):
        self.session = session
        self.token_repo = token_repo
        self.email_sender = email_sender

    async def request_recovery(self, email: str) -> bool:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        user = result.scalars().first()

        if not user:
            return True

        token = await self.token_repo.create(user.id)

        text = (
            "Восстановление пароля\n\n"
            f"Код восстановления:\n{token}\n\n"
            "Срок действия: 10 минут"
        )

        await self.email_sender.send(user.email, text)
        return True

    async def confirm_recovery(self, token: str, new_password: str) -> bool:
        user_id = await self.token_repo.consume(token)
        if not user_id:
            return False

        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalars().first()

        if not user:
            return False

        user.password = PasswordHasher.hash(new_password)
        await self.session.commit()
        return True
