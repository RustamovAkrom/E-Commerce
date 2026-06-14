"""Payment provider abstraction.

Each provider knows how to (a) start a payment — returning a hosted checkout
URL and/or form params — and (b) verify and interpret an asynchronous callback
from the provider, mapping it onto our :class:`PaymentStatus`.

Providers are pure integration adapters: they never touch the database. The
:class:`~src.modules.payments.service.PaymentService` orchestrates persistence
and order state changes around them.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from src.core.enums import PaymentProvider, PaymentStatus


@dataclass(slots=True)
class PaymentInitResult:
    """What a provider returns when a payment is started."""

    # Provider-side transaction id, if assigned synchronously (else filled by
    # the first webhook).
    provider_payment_id: str | None = None
    checkout_url: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WebhookResult:
    """Normalised outcome of a provider callback."""

    provider_payment_id: str
    status: PaymentStatus
    # The order this callback settles, when the provider echoes it back.
    order_id: str | None = None
    amount: Decimal | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class BasePaymentProvider(abc.ABC):
    """Common interface implemented by every concrete provider."""

    name: PaymentProvider

    @abc.abstractmethod
    async def create_payment(
        self,
        *,
        payment_id: str,
        order_id: str,
        amount: Decimal,
        currency: str,
        return_url: str | None,
    ) -> PaymentInitResult:
        """Initiate a payment and describe how the client should proceed."""

    @abc.abstractmethod
    async def parse_webhook(
        self, headers: dict[str, str], body: bytes
    ) -> WebhookResult:
        """Authenticate and decode a provider callback.

        Implementations MUST verify the provider's signature/credentials and
        raise :class:`~src.core.exceptions.PaymentError` on any mismatch.
        """
