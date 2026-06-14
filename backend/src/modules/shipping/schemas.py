"""Shipping Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from src.core.schemas import ORMSchema, StrictSchema
from src.modules.shipping.models import ShipmentStatus, ShippingMethod


# --- Address book -----------------------------------------------------------
class ShippingAddressCreateRequest(StrictSchema):
    label: str | None = Field(default=None, max_length=64)
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=3, max_length=32)
    address: str = Field(min_length=1, max_length=512)
    city: str = Field(min_length=1, max_length=128)
    country: str = Field(default="UZ", min_length=2, max_length=64)
    postal_code: str | None = Field(default=None, max_length=32)
    is_default: bool = False


class ShippingAddressUpdateRequest(StrictSchema):
    label: str | None = Field(default=None, max_length=64)
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=512)
    city: str | None = Field(default=None, max_length=128)
    country: str | None = Field(default=None, min_length=2, max_length=64)
    postal_code: str | None = Field(default=None, max_length=32)
    is_default: bool | None = None


class ShippingAddressResponse(ORMSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    label: str | None
    full_name: str
    phone: str
    address: str
    city: str
    country: str
    postal_code: str | None
    is_default: bool
    created_at: datetime


# --- Rate quotes ------------------------------------------------------------
class RateQuoteRequest(StrictSchema):
    country: str = Field(default="UZ", min_length=2, max_length=64)
    city: str = Field(min_length=1, max_length=128)
    method: ShippingMethod = ShippingMethod.STANDARD


class RateQuoteResponse(StrictSchema):
    method: ShippingMethod
    carrier: str
    cost: Decimal
    currency: str
    eta_days: int


# --- Shipments --------------------------------------------------------------
class ShipmentCreateRequest(StrictSchema):
    order_id: uuid.UUID
    method: ShippingMethod = ShippingMethod.STANDARD
    carrier: str | None = None


class ShipmentStatusUpdateRequest(StrictSchema):
    status: ShipmentStatus


class ShipmentResponse(ORMSchema):
    id: uuid.UUID
    order_id: uuid.UUID
    method: ShippingMethod
    status: ShipmentStatus
    carrier: str | None
    tracking_number: str | None
    cost: Decimal
    currency: str
    destination: dict
    created_at: datetime
