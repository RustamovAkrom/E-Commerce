"""Auth HTTP endpoints. Rate-limited on register/login."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from src.config import settings
from src.core.dependencies import DbSession, RedisClient, oauth2_scheme
from src.core.rate_limit import limiter
from src.core.schemas import MessageResponse
from src.modules.auth.schemas import (
    AuthResult,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TelegramAuthRequest,
    TokenPair,
)
from src.modules.auth.service import AuthService
from src.modules.users.schemas import UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResult,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    request: Request,
    data: RegisterRequest,
    db: DbSession,
    redis_client: RedisClient,
) -> AuthResult:
    from src.modules.users.schemas import UserCreateRequest

    user_create = UserCreateRequest(
        email=data.email,
        username=data.username,
        password=data.password,
        full_name=data.full_name,
        phone=data.phone,
    )
    user, tokens = await AuthService(db, redis_client).register(user_create)
    return AuthResult(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/login", response_model=AuthResult)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    db: DbSession,
    redis_client: RedisClient,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> AuthResult:
    # Accept username OR email in the OAuth2 ``username`` field
    user, tokens = await AuthService(db, redis_client).login(
        form.username, form.password
    )
    return AuthResult(user=UserResponse.model_validate(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    data: RefreshRequest,
    db: DbSession,
    redis_client: RedisClient,
) -> TokenPair:
    return await AuthService(db, redis_client).refresh(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: LogoutRequest,
    db: DbSession,
    redis_client: RedisClient,
    access_token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> MessageResponse:
    await AuthService(db, redis_client).logout(
        access_token or "", data.refresh_token
    )
    return MessageResponse(message="Logged out.")


@router.post("/telegram", response_model=AuthResult)
async def telegram_auth(
    data: TelegramAuthRequest,
    db: DbSession,
    redis_client: RedisClient,
) -> AuthResult:
    user, tokens = await AuthService(db, redis_client).telegram_login(
        data.telegram_id, data.full_name, data.auth_secret
    )
    return AuthResult(user=UserResponse.model_validate(user), tokens=tokens)
