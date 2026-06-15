"""SMTP email channel.

Sends via the configured SMTP server using the stdlib ``smtplib`` (run in a
worker thread so the event loop is never blocked). If SMTP is not configured
the channel reports a soft failure rather than raising, so a missing mail
server degrades gracefully in development.
"""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from src.config import settings
from src.modules.notifications.channels.base import BaseChannel, DeliveryResult


class EmailChannel(BaseChannel):
    name = "email"

    def _send_sync(
        self, destination: str, subject: str | None, body: str
    ) -> None:
        message = EmailMessage()
        message["From"] = settings.SMTP_FROM
        message["To"] = destination
        message["Subject"] = subject or settings.APP_NAME
        message.set_content(body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            if settings.SMTP_TLS:
                smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)

    async def send(
        self,
        *,
        destination: str,
        subject: str | None,
        body: str,
    ) -> DeliveryResult:
        if not settings.SMTP_HOST:
            return DeliveryResult(
                success=False, detail="SMTP host is not configured."
            )
        try:
            await asyncio.to_thread(self._send_sync, destination, subject, body)
        except Exception as exc:  # noqa: BLE001 - report, never propagate
            return DeliveryResult(success=False, detail=str(exc))
        return DeliveryResult(success=True)
