"""Security primitives: password hashing and JWT encode/decode.

Pure functions only — no DB or Redis access here. Token persistence and
blacklisting live in the auth service.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from passlib.context import CryptContext

from src.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


# --- Passwords --------------------------------------------------------------
def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# --- JWT --------------------------------------------------------------------
def _create_token(
    subject: str,
    token_type: TokenType,
    ttl_seconds: int,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return ``(encoded_jwt, jti)``.

    The ``jti`` (token id) lets the auth service track / revoke tokens.
    """
    now = datetime.now(UTC)
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(seconds=ttl_seconds),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_access_token(
    subject: str, extra_claims: dict[str, Any] | None = None
) -> tuple[str, str]:
    return _create_token(
        subject, TokenType.ACCESS, settings.ACCESS_TOKEN_TTL_SECONDS, extra_claims
    )


def create_refresh_token(subject: str) -> tuple[str, str]:
    return _create_token(subject, TokenType.REFRESH, settings.REFRESH_TOKEN_TTL_SECONDS)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising ``jwt.PyJWTError`` on failure."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
