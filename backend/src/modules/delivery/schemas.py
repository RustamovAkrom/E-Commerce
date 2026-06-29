"""Delivery Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from src.core.schemas import ORMSchema, StrictSchema


class CourierResponse(ORMSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    phone: str | None
    zone: str | None
    is_active: bool


class CourierCreateRequest(StrictSchema):
    user_id: uuid.UUID
    phone: str | None = Field(default=None, max_length=32)
    zone: str | None = Field(default=None, max_length=128)


class CourierUpdateRequest(StrictSchema):
    phone: str | None = Field(default=None, max_length=32)
    zone: str | None = Field(default=None, max_length=128)
    is_active: bool | None = None


class DeliveryAssignmentResponse(ORMSchema):
    id: uuid.UUID
    order_id: uuid.UUID
    courier_id: uuid.UUID | None
    courier_name: str | None
    status: str
    created_at: datetime


class CourierDeliveryResponse(StrictSchema):
    """A delivery enriched with everything a courier needs in the field: the
    destination address (for map navigation), customer contact and the order
    amount to collect.
    """

    id: uuid.UUID
    order_id: uuid.UUID
    status: str
    created_at: datetime
    # Destination — sourced from the order's shipping-address snapshot.
    customer_name: str
    phone: str | None
    address: str
    city: str
    country: str
    postal_code: str | None
    total_amount: Decimal
    currency: str
