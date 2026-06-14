"""Shipping carrier registry.

The active carrier is resolved by name. A single ``local_courier`` ships by
default; additional carriers register here.
"""

from __future__ import annotations

from src.modules.shipping.providers.base import (
    BaseShippingProvider,
    RateQuote,
    ShipmentDraft,
)
from src.modules.shipping.providers.local import LocalCourierProvider

_REGISTRY: dict[str, BaseShippingProvider] = {
    LocalCourierProvider.name: LocalCourierProvider(),
}

DEFAULT_CARRIER = LocalCourierProvider.name


def get_carrier(name: str | None = None) -> BaseShippingProvider:
    return _REGISTRY[name or DEFAULT_CARRIER]


__all__ = [
    "BaseShippingProvider",
    "RateQuote",
    "ShipmentDraft",
    "DEFAULT_CARRIER",
    "get_carrier",
]
