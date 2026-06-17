"""User Pydantic schemas (separate Request / Response / Update)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from src.core.enums import UserRole
from src.core.schemas import ORMSchema, StrictSchema


class UserCreateRequest(StrictSchema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class UserUpdateRequest(StrictSchema):
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class UserAdminUpdateRequest(StrictSchema):
    role: UserRole | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class PasswordChangeRequest(StrictSchema):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(ORMSchema):
    id: uuid.UUID
    email: str
    full_name: str | None
    phone: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
