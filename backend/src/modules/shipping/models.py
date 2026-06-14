"""Shipping ORM models.

Two concerns live here:

* :class:`ShippingAddress` — a customer's reusable address book entry.
* :class:`Shipment` — the delivery of a specific order via a carrier, carrying a
  tracking number and a denormalised snapshot of the destination address.

Following the project convention (see ``inventory.models``) the shipping status
and method enums are defined locally rather than in ``core.enums`` since they
are only meaningful within this module.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.core.database import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

JSONType = JSON().with_variant(JSONB(), "postgresql")


class ShippingMethod(StrEnum):
    STANDARD = "standard"
    EXPRESS = "express"
    PICKUP = "pickup"


class ShipmentStatus(StrEnum):
    PENDING = "pending"
    LABEL_CREATED = "label_created"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class ShippingAddress(
    UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base
):
    __tablename__ = "shipping_addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    country: Mapped[str] = mapped_column(String(64), default="UZ", nullable=False)
    postal_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )


class Shipment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "shipments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    method: Mapped[ShippingMethod] = mapped_column(
        Enum(ShippingMethod, native_enum=False, length=32),
        default=ShippingMethod.STANDARD,
        nullable=False,
    )
    status: Mapped[ShipmentStatus] = mapped_column(
        Enum(ShipmentStatus, native_enum=False, length=32),
        default=ShipmentStatus.PENDING,
        nullable=False,
        index=True,
    )
    carrier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(
        String(128), index=True, nullable=True
    )
    cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)
    # Snapshot of the destination at the time the shipment was created.
    destination: Mapped[dict] = mapped_column(JSONType, nullable=False)
