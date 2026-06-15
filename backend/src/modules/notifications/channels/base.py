"""Notification channel abstraction.

A channel knows how to deliver a rendered message to one destination over one
transport (email, SMS, Telegram). Channels are pure integration adapters: they
never touch the database. The service records the audit row and decides which
channel to use.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass(slots=True)
class DeliveryResult:
    """Outcome of a single delivery attempt."""

    success: bool
    detail: str | None = None


class BaseChannel(abc.ABC):
    name: str

    @abc.abstractmethod
    async def send(
        self,
        *,
        destination: str,
        subject: str | None,
        body: str,
    ) -> DeliveryResult:
        """Deliver ``body`` to ``destination``; never raises, returns result."""
