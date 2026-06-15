"""Vendor Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import EmailStr, Field

from src.core.schemas import ORMSchema, StrictSchema
from src.modules.vendors.models import VendorStatus


class VendorApplyRequest(StrictSchema):
    """A user applies to become a vendor."""

    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=4000)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)


class VendorUpdateRequest(StrictSchema):
    """A vendor edits its own storefront profile."""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    logo_url: str | None = Field(default=None, max_length=1024)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)


class VendorAdminUpdateRequest(StrictSchema):
    """Admin moderation of a vendor."""

    status: VendorStatus | None = None
    is_active: bool | None = None
    commission_rate: Decimal | None = Field(default=None, ge=0, le=100)


class VendorResponse(ORMSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    contact_email: str | None
    contact_phone: str | None
    status: VendorStatus
    is_active: bool
    commission_rate: Decimal
    created_at: datetime


class VendorPublicResponse(ORMSchema):
    """The subset of vendor data exposed to the public storefront."""

    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    logo_url: str | None
