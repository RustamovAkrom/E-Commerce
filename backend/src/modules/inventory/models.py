"""Inventory ORM models.

A ``StockMovement`` is an append-only ledger entry recording every change to a
product's stock (restock, sale, reservation release, manual adjustment). The
product's ``stock`` column is the materialised current value.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MovementReason(StrEnum):
    RESTOCK = "restock"
    SALE = "sale"
    RESERVATION = "reservation"
    RELEASE = "release"
    ADJUSTMENT = "adjustment"


class StockMovement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stock_movements"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Positive = stock added, negative = stock removed.
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[MovementReason] = mapped_column(
        Enum(MovementReason, native_enum=False, length=32),
        nullable=False,
    )
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
