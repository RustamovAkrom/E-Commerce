"""Shipping carrier abstraction.

A carrier provides a rate *quote* for a destination + method and creates a
*shipment* (assigning a tracking number). Concrete carriers are integration
adapters and never touch the database.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from decimal import Decimal

from src.modules.shipping.models import ShippingMethod


@dataclass(slots=True)
class RateQuote:
    method: ShippingMethod
    carrier: str
    cost: Decimal
    currency: str
    eta_days: int


@dataclass(slots=True)
class ShipmentDraft:
    carrier: str
    tracking_number: str


class BaseShippingProvider(abc.ABC):
    name: str

    @abc.abstractmethod
    def quote(
        self, *, country: str, city: str, method: ShippingMethod
    ) -> RateQuote:
        """Return a price quote for delivering to ``city``/``country``."""

    @abc.abstractmethod
    def create_shipment(
        self, *, order_id: str, country: str, city: str, method: ShippingMethod
    ) -> ShipmentDraft:
        """Register a shipment with the carrier and return its tracking id."""
