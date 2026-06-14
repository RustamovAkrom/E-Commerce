"""Payment ORM model.

A ``Payment`` records a single attempt to settle an order through one of the
configured providers (Click, Payme, Stripe). The provider's own transaction id
and the raw callback payload are stored so reconciliation and idempotent
webhook handling are possible.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.core.database import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from src.core.enums import PaymentProvider, PaymentStatus

# Use JSONB on PostgreSQL, fall back to generic JSON elsewhere (SQLite tests).
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        # A provider transaction id is globally unique within a provider; this
        # makes webhook processing naturally idempotent.
        UniqueConstraint(
            "provider", "provider_payment_id", name="uq_payment_provider_txn"
        ),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, length=32),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)
    # The provider-side identifier for this transaction (filled once known).
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(255), index=True, nullable=True
    )
    # Last raw provider payload (init response or webhook), for audit/debug.
    raw_payload: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
