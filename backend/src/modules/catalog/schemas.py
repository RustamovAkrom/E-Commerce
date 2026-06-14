"""Catalog Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from src.core.schemas import ORMSchema, StrictSchema


# --- Category ---------------------------------------------------------------
class CategoryCreateRequest(StrictSchema):
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    parent_id: uuid.UUID | None = None
    sort_order: int = 0
    is_active: bool = True


class CategoryUpdateRequest(StrictSchema):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    parent_id: uuid.UUID | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryResponse(ORMSchema):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    parent_id: uuid.UUID | None
    sort_order: int
    is_active: bool


# --- Product images / attributes -------------------------------------------
class ProductImageResponse(ORMSchema):
    id: uuid.UUID
    url: str
    is_primary: bool
    sort_order: int


class ProductAttributeRequest(StrictSchema):
    key: str = Field(min_length=1, max_length=128)
    value: str = Field(min_length=1, max_length=512)


class ProductAttributeResponse(ORMSchema):
    id: uuid.UUID
    key: str
    value: str


# --- Product ----------------------------------------------------------------
class ProductCreateRequest(StrictSchema):
    category_id: uuid.UUID
    vendor_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    sku: str | None = Field(default=None, max_length=64)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="UZS", min_length=3, max_length=3)
    stock: int = Field(default=0, ge=0)
    is_active: bool = True
    attributes: list[ProductAttributeRequest] = Field(default_factory=list)


class ProductUpdateRequest(StrictSchema):
    category_id: uuid.UUID | None = None
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    sku: str | None = Field(default=None, max_length=64)
    price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(ORMSchema):
    id: uuid.UUID
    vendor_id: uuid.UUID | None
    category_id: uuid.UUID
    name: str
    slug: str
    description: str | None
    sku: str | None
    price: Decimal
    currency: str
    stock: int
    is_active: bool
    created_at: datetime


class ProductDetailResponse(ProductResponse):
    images: list[ProductImageResponse] = Field(default_factory=list)
    attributes: list[ProductAttributeResponse] = Field(default_factory=list)
