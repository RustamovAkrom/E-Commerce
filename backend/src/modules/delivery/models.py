"""Delivery ORM models: Courier and DeliveryAssignment.

A ``Courier`` is a user account (1:1 with a COURIER-role User) that can
accept delivery assignments. A ``DeliveryAssignment`` links an order to a
courier and tracks the delivery lifecycle.
"""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class DeliveryStatus(StrEnum):
    PENDING = "pending"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Courier(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "couriers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Geographic zone this courier serves (e.g. "Tashkent-Center").
    zone: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    user: Mapped[User] = relationship("User")  # type: ignore[name-defined]
    assignments: Mapped[list[DeliveryAssignment]] = relationship(
        "DeliveryAssignment",
        back_populates="courier",
        cascade="all, delete-orphan",
    )


class DeliveryAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "delivery_assignments"

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    courier_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("couriers.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus, native_enum=False, length=32),
        default=DeliveryStatus.PENDING,
        nullable=False,
        index=True,
    )

    order: Mapped[Order] = relationship("Order")  # type: ignore[name-defined]
    courier: Mapped[Courier] = relationship(
        "Courier", back_populates="assignments"
    )
