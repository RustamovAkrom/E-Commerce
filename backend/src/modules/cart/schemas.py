"""Cart Pydantic schemas. The cart itself lives in Redis (no SQL model)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from src.core.schemas import StrictSchema


class CartItemRequest(StrictSchema):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=999)


class CartItemResponse(BaseModel):
    product_id: uuid.UUID
    name: str
    slug: str
    unit_price: Decimal
    currency: str
    quantity: int
    line_total: Decimal
    available_stock: int


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    total_items: int
    subtotal: Decimal
    currency: str
