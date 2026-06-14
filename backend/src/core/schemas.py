"""Base Pydantic schemas shared across modules."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMSchema(BaseModel):
    """Base for response schemas read from ORM objects."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class StrictSchema(BaseModel):
    """Base for request schemas — forbids unexpected fields."""

    model_config = ConfigDict(extra="forbid")


class TimestampedSchema(ORMSchema):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Generic ``{"message": "..."}`` response."""

    message: str
