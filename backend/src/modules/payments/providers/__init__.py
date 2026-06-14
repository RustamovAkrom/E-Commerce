"""Payment provider registry.

Maps a :class:`PaymentProvider` enum value to its concrete adapter instance so
the service can dispatch without ``if/elif`` chains.
"""

from __future__ import annotations

from src.core.enums import PaymentProvider
from src.core.exceptions import ValidationError
from src.modules.payments.providers.base import (
    BasePaymentProvider,
    PaymentInitResult,
    WebhookResult,
)
from src.modules.payments.providers.click import ClickProvider
from src.modules.payments.providers.payme import PaymeProvider
from src.modules.payments.providers.stripe import StripeProvider

_REGISTRY: dict[PaymentProvider, BasePaymentProvider] = {
    PaymentProvider.CLICK: ClickProvider(),
    PaymentProvider.PAYME: PaymeProvider(),
    PaymentProvider.STRIPE: StripeProvider(),
}


def get_provider(provider: PaymentProvider) -> BasePaymentProvider:
    adapter = _REGISTRY.get(provider)
    if adapter is None:  # pragma: no cover - guarded by enum validation
        raise ValidationError(f"Unsupported payment provider '{provider}'.")
    return adapter


__all__ = [
    "BasePaymentProvider",
    "PaymentInitResult",
    "WebhookResult",
    "get_provider",
]
