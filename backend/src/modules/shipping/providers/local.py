"""Local courier carrier.

A self-contained, zone-based flat-rate carrier suitable for the default
single-country (Uzbekistan) deployment. Rates are computed from a small zone
table plus a per-method multiplier — no external API call required, which keeps
checkout fast and the platform usable out of the box. Real carriers (BTS,
Uzpost, DHL) can be added as sibling adapters implementing the same interface.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from src.modules.shipping.models import ShippingMethod
from src.modules.shipping.providers.base import (
    BaseShippingProvider,
    RateQuote,
    ShipmentDraft,
)

# Base delivery cost (UZS) and ETA by destination zone.
_DOMESTIC_BASE = Decimal("25000")
_INTERNATIONAL_BASE = Decimal("250000")

# Capital city gets the cheapest, fastest domestic tier.
_CAPITAL_CITIES = {"tashkent", "toshkent"}

_METHOD_MULTIPLIER: dict[ShippingMethod, Decimal] = {
    ShippingMethod.STANDARD: Decimal("1.0"),
    ShippingMethod.EXPRESS: Decimal("2.0"),
    ShippingMethod.PICKUP: Decimal("0.0"),
}

_METHOD_ETA_DAYS: dict[ShippingMethod, int] = {
    ShippingMethod.STANDARD: 4,
    ShippingMethod.EXPRESS: 1,
    ShippingMethod.PICKUP: 0,
}


class LocalCourierProvider(BaseShippingProvider):
    name = "local_courier"

    def _base_cost(self, country: str, city: str) -> Decimal:
        if country.upper() not in {"UZ", "UZB"}:
            return _INTERNATIONAL_BASE
        if city.strip().lower() in _CAPITAL_CITIES:
            return _DOMESTIC_BASE * Decimal("0.6")
        return _DOMESTIC_BASE

    def quote(
        self, *, country: str, city: str, method: ShippingMethod
    ) -> RateQuote:
        base = self._base_cost(country, city)
        cost = (base * _METHOD_MULTIPLIER[method]).quantize(Decimal("1"))
        return RateQuote(
            method=method,
            carrier=self.name,
            cost=cost,
            currency="UZS",
            eta_days=_METHOD_ETA_DAYS[method],
        )

    def create_shipment(
        self, *, order_id: str, country: str, city: str, method: ShippingMethod
    ) -> ShipmentDraft:
        # A real carrier returns the tracking id from its API; locally we mint a
        # deterministic-looking one.
        tracking = f"LC{uuid.uuid4().hex[:12].upper()}"
        return ShipmentDraft(carrier=self.name, tracking_number=tracking)
