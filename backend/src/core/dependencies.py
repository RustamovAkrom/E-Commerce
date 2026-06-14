"""Shared FastAPI dependencies: DB session, current user, RBAC guards.

These are imported by every module router. Authentication decodes the JWT,
checks the Redis blacklist, and loads the user from the database.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import jwt
import redis.asyncio as redis
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.database import async_session_maker
from src.core.enums import ROLE_RANK, UserRole
from src.core.exceptions import AuthenticationError, PermissionDeniedError
from src.core.redis import get_redis
from src.core.security import TokenType, decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)

# Redis key prefix for blacklisted access-token jti values.
BLACKLIST_PREFIX = "blacklist:access:"


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional session; commit on success, rollback on error."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_redis_client() -> redis.Redis:
    return get_redis()


DbSession = Annotated[AsyncSession, Depends(get_db)]
RedisClient = Annotated[redis.Redis, Depends(get_redis_client)]


async def get_current_user(
    db: DbSession,
    redis_client: RedisClient,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
):
    """Resolve the authenticated :class:`User` from a bearer access token."""
    # Imported lazily to avoid a circular import (users -> core -> users).
    from src.modules.users.models import User

    if not token:
        raise AuthenticationError("Not authenticated.")

    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Invalid or expired token.") from exc

    if payload.get("type") != TokenType.ACCESS.value:
        raise AuthenticationError("Wrong token type.")

    jti = payload.get("jti")
    if jti and await redis_client.exists(f"{BLACKLIST_PREFIX}{jti}"):
        raise AuthenticationError("Token has been revoked.")

    subject = payload.get("sub")
    if not subject:
        raise AuthenticationError("Malformed token.")

    user = await db.get(User, uuid.UUID(subject))
    if user is None or user.is_deleted or not user.is_active:
        raise AuthenticationError("User not found or inactive.")
    return user


CurrentUser = Annotated["object", Depends(get_current_user)]


def require_role(*allowed: UserRole):
    """Dependency factory enforcing that the user has *at least* one role.

    Hierarchical: a SUPERADMIN satisfies a require_role(ADMIN) check.
    """
    min_rank = min(ROLE_RANK[r] for r in allowed)

    async def _guard(user: CurrentUser):  # type: ignore[valid-type]
        user_rank = ROLE_RANK.get(user.role, -1)  # type: ignore[attr-defined]
        if user_rank < min_rank:
            raise PermissionDeniedError(
                "Insufficient role.",
                details={"required": [r.value for r in allowed]},
            )
        return user

    return _guard


# Convenience pre-built guards.
require_admin = require_role(UserRole.ADMIN)
require_superadmin = require_role(UserRole.SUPERADMIN)
