"""Inventory Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from src.core.schemas import ORMSchema, StrictSchema
from src.modules.inventory.models import MovementReason


class StockAdjustRequest(StrictSchema):
    product_id: uuid.UUID
    delta: int = Field(description="Positive to add stock, negative to remove")
    reason: MovementReason = MovementReason.ADJUSTMENT
    reference: str | None = Field(default=None, max_length=255)


class StockMovementResponse(ORMSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    delta: int
    reason: MovementReason
    reference: str | None
    created_at: datetime


class StockLevelResponse(ORMSchema):
    product_id: uuid.UUID
    stock: int
