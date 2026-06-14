"""Auth Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from src.core.schemas import StrictSchema
from src.modules.users.schemas import UserResponse


class RegisterRequest(StrictSchema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=32)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token TTL in seconds


class RefreshRequest(StrictSchema):
    refresh_token: str


class LogoutRequest(StrictSchema):
    refresh_token: str


class TelegramAuthRequest(StrictSchema):
    """Sent by the bot (server-to-server) to provision/login a TG user."""

    telegram_id: int
    full_name: str | None = Field(default=None, max_length=255)
    auth_secret: str  # shared secret, verified against settings


class AuthResult(BaseModel):
    user: UserResponse
    tokens: TokenPair
