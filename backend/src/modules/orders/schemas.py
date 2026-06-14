"""Order Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from src.core.enums import OrderStatus
from src.core.schemas import ORMSchema, StrictSchema


class ShippingAddressInput(StrictSchema):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=3, max_length=32)
    address: str = Field(min_length=1, max_length=512)
    city: str = Field(min_length=1, max_length=128)
    country: str = Field(default="UZ", min_length=2, max_length=64)
    postal_code: str | None = Field(default=None, max_length=32)


class OrderCreateRequest(StrictSchema):
    """Create an order from the caller's current cart."""

    shipping_address: ShippingAddressInput
    note: str | None = Field(default=None, max_length=1024)


class OrderStatusUpdateRequest(StrictSchema):
    status: OrderStatus


class OrderItemResponse(ORMSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: Decimal


class OrderResponse(ORMSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    currency: str
    shipping_address: dict
    note: str | None
    created_at: datetime


class OrderDetailResponse(OrderResponse):
    items: list[OrderItemResponse] = Field(default_factory=list)
