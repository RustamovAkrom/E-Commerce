"""Notification channel registry.

Resolves a :class:`NotificationChannel` enum value to its channel adapter. The
adapters are stateful singletons (they cache auth tokens), so they are
instantiated once here and reused.
"""

from __future__ import annotations

from src.core.enums import NotificationChannel
from src.modules.notifications.channels.base import BaseChannel, DeliveryResult
from src.modules.notifications.channels.email import EmailChannel
from src.modules.notifications.channels.sms import SMSChannel
from src.modules.notifications.channels.telegram import TelegramChannel

_REGISTRY: dict[NotificationChannel, BaseChannel] = {
    NotificationChannel.EMAIL: EmailChannel(),
    NotificationChannel.SMS: SMSChannel(),
    NotificationChannel.TELEGRAM: TelegramChannel(),
}


def get_channel(channel: NotificationChannel) -> BaseChannel:
    return _REGISTRY[channel]


__all__ = [
    "BaseChannel",
    "DeliveryResult",
    "get_channel",
]
