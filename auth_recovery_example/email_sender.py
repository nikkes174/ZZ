from abc import ABC, abstractmethod
from email.message import EmailMessage

import aiosmtplib


class EmailSender(ABC):
    @abstractmethod
    async def send(self, email: str, text: str): ...


class EmailDeliveryError(Exception):
    pass


class SMTPEmailSender(EmailSender):
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_email: str,
        *,
        use_tls: bool = True,
    ) -> None:

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    async def send(self, email: str, text: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.from_email
        msg["To"] = email
        msg["Subject"] = "Восстановление пароля"
        msg.set_content(text)

        try:
            await aiosmtplib.send(
                msg,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=self.use_tls,
                timeout=10,
            )
        except (aiosmtplib.SMTPException, TimeoutError, OSError) as e:
            raise EmailDeliveryError("Не удалось отправить письмо") from e
