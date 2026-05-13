from __future__ import annotations

import asyncio
import socket
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage


class EmailDeliveryError(Exception):
    pass


def _create_ipv4_connection(
    host: str,
    port: int,
    timeout: int,
    source_address: tuple[str, int] | None = None,
) -> socket.socket:
    errors: list[OSError] = []
    for family, socket_type, proto, _, address in socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM):
        sock = socket.socket(family, socket_type, proto)
        sock.settimeout(timeout)
        try:
            if source_address:
                sock.bind(source_address)
            sock.connect(address)
            return sock
        except OSError as exc:
            errors.append(exc)
            sock.close()

    if errors:
        raise errors[-1]
    raise OSError(f"No IPv4 address found for {host}")


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host: str, port: int, timeout: int) -> socket.socket:
        return _create_ipv4_connection(host, port, timeout, self.source_address)


class IPv4SMTPSSL(smtplib.SMTP_SSL):
    def _get_socket(self, host: str, port: int, timeout: int) -> socket.socket:
        raw_socket = _create_ipv4_connection(host, port, timeout, self.source_address)
        return self.context.wrap_socket(raw_socket, server_hostname=host)


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
    force_ipv4: bool = True

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
        if self.use_ssl:
            smtp_class = IPv4SMTPSSL if self.force_ipv4 else smtplib.SMTP_SSL
        else:
            smtp_class = IPv4SMTP if self.force_ipv4 else smtplib.SMTP
        with smtp_class(self.host, self.port, timeout=self.timeout_seconds) as smtp:
            if self.use_tls and not self.use_ssl:
                smtp.starttls()
            smtp.login(self.username, self.password)
            smtp.send_message(message)
