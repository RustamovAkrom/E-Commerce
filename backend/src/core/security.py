"""Security primitives: password hashing and JWT encode/decode.

Pure functions only — no DB or Redis access here. Token persistence and
blacklisting live in the auth service.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import bcrypt
import jwt

from src.config import settings


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


# --- Passwords --------------------------------------------------------------
# bcrypt operates on at most 72 bytes; longer inputs are silently truncated by
# the algorithm, so we truncate explicitly to keep hashing and verification
# consistent (passlib is unmaintained and incompatible with bcrypt >= 4).
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(plain: str) -> bytes:
    return plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(plain: str) -> str:
    hashed = bcrypt.hashpw(_to_bcrypt_bytes(plain), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_bytes(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


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
