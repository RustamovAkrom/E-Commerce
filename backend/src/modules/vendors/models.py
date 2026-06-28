"""Vendor ORM model.

Defined unconditionally (so ``Product.vendor_id`` always has a FK target and
Alembic sees a stable schema), but the vendor *router* is only mounted when
``MARKETPLACE_MODE`` is enabled. A vendor is owned 1:1 by a user with the
``VENDOR`` role and carries a moderation status governing whether its products
are publicly listable.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String, Text, event, select
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.core.database import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from src.core.utils import generate_slug
from src.modules.users.models import User


class VendorStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class Vendor(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "vendors"

    # The user account that owns / operates this vendor storefront.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus, native_enum=False, length=32),
        default=VendorStatus.PENDING,
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Platform commission percentage (e.g. 10.00 = 10%).
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0"), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="vendor")

    @validates("name")
    def _generate_slug_from_name(self, key: str, name: str) -> str:  # noqa: ARG002
        self.slug = generate_slug(name)
        return name


@event.listens_for(Vendor, "before_insert")
@event.listens_for(Vendor, "before_update")
def _set_unique_vendor_slug(mapper: Any, connection: Any, target: Vendor) -> None:  # noqa: ARG001
    stmt = select(Vendor.slug).where(Vendor.is_deleted.is_(False))
    if target.id is not None:
        stmt = stmt.where(Vendor.id != target.id)
    existing_slugs = set(connection.execute(stmt).scalars().all())
    target.slug = generate_slug(target.name, existing_slugs)
