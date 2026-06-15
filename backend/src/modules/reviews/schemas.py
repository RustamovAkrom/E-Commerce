"""Review Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from src.core.schemas import ORMSchema, StrictSchema


class ReviewCreateRequest(StrictSchema):
    rating: int = Field(ge=1, le=5)
    title: str | None = Field(default=None, max_length=255)
    comment: str | None = Field(default=None, max_length=4000)


class ReviewUpdateRequest(StrictSchema):
    rating: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, max_length=255)
    comment: str | None = Field(default=None, max_length=4000)


class ReviewModerateRequest(StrictSchema):
    is_approved: bool


class ReviewResponse(ORMSchema):
    id: uuid.UUID
    product_id: uuid.UUID
    user_id: uuid.UUID
    rating: int
    title: str | None
    comment: str | None
    is_approved: bool
    created_at: datetime


class ProductRatingSummary(StrictSchema):
    product_id: uuid.UUID
    average_rating: float
    review_count: int
