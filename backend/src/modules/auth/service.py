"""Authentication logic: token issuance, refresh rotation, revocation.

Refresh tokens are stored in Redis keyed by their ``jti`` so they can be
rotated and revoked. On every refresh the old token is invalidated and a new
pair is issued (refresh-token rotation). Access tokens are stateless but their
``jti`` can be blacklisted on logout until they naturally expire.
"""

from __future__ import annotations

import hmac
import uuid

import jwt
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.dependencies import BLACKLIST_PREFIX
from src.core.enums import UserRole
from src.core.exceptions import AuthenticationError
from src.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.modules.auth.schemas import (
    RegisterRequest,
    TokenPair,
)
from src.modules.users.models import User
from src.modules.users.schemas import UserCreateRequest
from src.modules.users.service import UserService

REFRESH_PREFIX = "refresh:"


class AuthService:
    def __init__(self, session: AsyncSession, redis_client: redis.Redis) -> None:
        self.session = session
        self.redis = redis_client
        self.users = UserService(session)

    # --- Token helpers ------------------------------------------------------
    async def _issue_pair(self, user: User) -> TokenPair:
        access, _ = create_access_token(
            str(user.id), extra_claims={"role": user.role.value}
        )
        refresh, refresh_jti = create_refresh_token(str(user.id))
        # Store the active refresh jti so it can be rotated/revoked.
        await self.redis.set(
            f"{REFRESH_PREFIX}{refresh_jti}",
            str(user.id),
            ex=settings.REFRESH_TOKEN_TTL_SECONDS,
        )
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.ACCESS_TOKEN_TTL_SECONDS,
        )

    # --- Public flows -------------------------------------------------------
    async def register(self, data: RegisterRequest) -> tuple[User, TokenPair]:
        user = await self.users.create(
            UserCreateRequest(
                email=data.email,
                password=data.password,
                full_name=data.full_name,
                phone=data.phone,
            ),
            role=UserRole.CUSTOMER,
        )
        tokens = await self._issue_pair(user)
        return user, tokens

    async def login(self, email: str, password: str) -> tuple[User, TokenPair]:
        user = await self.users.authenticate(email, password)
        if user is None:
            raise AuthenticationError("Incorrect email or password.")
        tokens = await self._issue_pair(user)
        return user, tokens

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise AuthenticationError("Invalid refresh token.") from exc

        if payload.get("type") != TokenType.REFRESH.value:
            raise AuthenticationError("Wrong token type.")

        jti = payload.get("jti")
        if not jti:
            raise AuthenticationError("Invalid refresh token.")

        stored = await self.redis.get(f"{REFRESH_PREFIX}{jti}")
        if stored is None:
            raise AuthenticationError("Refresh token has been revoked or expired.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Invalid refresh token.")

        try:
            user_id = uuid.UUID(user_id_str)
        except (ValueError, AttributeError):
            raise AuthenticationError("Invalid refresh token.") from None

        user = await self.users.get(user_id)
        if not user:
            raise AuthenticationError("User not found.")
        if not user.is_active:
            raise AuthenticationError("User is inactive.")

        # Rotate: invalidate the presented refresh token.
        await self.redis.delete(f"{REFRESH_PREFIX}{jti}")

        return await self._issue_pair(user)

    async def logout(self, access_token: str, refresh_token: str) -> None:
        """Blacklist the access token and drop the refresh token."""
        try:
            access_payload = decode_token(access_token)
            access_jti = access_payload.get("jti")
            # Blacklist until the access token would have expired anyway.
            ttl = settings.ACCESS_TOKEN_TTL_SECONDS
            if access_jti:
                await self.redis.set(
                    f"{BLACKLIST_PREFIX}{access_jti}", "1", ex=ttl
                )
        except jwt.PyJWTError:
            pass  # an unparseable access token is already useless

        try:
            refresh_payload = decode_token(refresh_token)
            refresh_jti = refresh_payload.get("jti")
            if refresh_jti:
                await self.redis.delete(f"{REFRESH_PREFIX}{refresh_jti}")
        except jwt.PyJWTError:
            pass

    async def telegram_login(
        self, telegram_id: int, full_name: str | None, auth_secret: str
    ) -> tuple[User, TokenPair]:
        if not settings.TELEGRAM_AUTH_SECRET or not hmac.compare_digest(
            auth_secret, settings.TELEGRAM_AUTH_SECRET
        ):
            raise AuthenticationError("Invalid Telegram auth secret.")
        user = await self.users.get_or_create_telegram_user(telegram_id, full_name)
        tokens = await self._issue_pair(user)
        return user, tokens
