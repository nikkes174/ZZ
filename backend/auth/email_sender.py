from __future__ import annotations

import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage


class EmailDeliveryError(Exception):
    pass


@dataclass
class SMTPEmailSender:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    use_tls: bool = True
    use_ssl: bool = False
    timeout_seconds: int = 10

    async def send(self, *, email: str, subject: str, text: str) -> None:
        if not self.host or not self.port or not self.username or not self.password or not self.from_email:
            raise EmailDeliveryError("SMTP is not configured: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD and SMTP_FROM are required")

        message = EmailMessage()
        message["From"] = self.from_email
        message["To"] = email
        message["Subject"] = subject
        message.set_content(text)

        try:
            await asyncio.to_thread(self._send_sync, message)
        except (smtplib.SMTPException, TimeoutError, OSError) as exc:
            raise EmailDeliveryError("Failed to send email") from exc

    def _send_sync(self, message: EmailMessage) -> None:
        smtp_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        with smtp_class(self.host, self.port, timeout=self.timeout_seconds) as smtp:
            if self.use_tls and not self.use_ssl:
                smtp.starttls()
            smtp.login(self.username, self.password)
            smtp.send_message(message)
