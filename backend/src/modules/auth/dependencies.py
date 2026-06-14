"""Auth module-specific dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.core.dependencies import DbSession, RedisClient
from src.modules.auth.service import AuthService


def get_auth_service(db: DbSession, redis_client: RedisClient) -> AuthService:
    return AuthService(db, redis_client)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
