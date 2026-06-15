"""Telegram channel via the Bot API.

Sends a message to a chat id using the configured bot token over the Telegram
HTTP Bot API. The destination is the numeric Telegram chat/user id. Missing a
bot token degrades to a soft failure rather than raising.
"""

from __future__ import annotations

import httpx

from src.config import settings
from src.modules.notifications.channels.base import BaseChannel, DeliveryResult


class TelegramChannel(BaseChannel):
    name = "telegram"

    async def send(
        self,
        *,
        destination: str,
        subject: str | None,
        body: str,
    ) -> DeliveryResult:
        if not settings.BOT_TOKEN:
            return DeliveryResult(
                success=False, detail="Telegram bot token is not configured."
            )
        text = f"*{subject}*\n\n{body}" if subject else body
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": destination,
                        "text": text,
                        "parse_mode": "Markdown",
                    },
                )
                if resp.status_code != httpx.codes.OK:
                    return DeliveryResult(
                        success=False,
                        detail=f"Telegram API returned {resp.status_code}.",
                    )
        except Exception as exc:  # noqa: BLE001 - report, never propagate
            return DeliveryResult(success=False, detail=str(exc))
        return DeliveryResult(success=True)
