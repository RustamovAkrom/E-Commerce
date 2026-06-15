"""Authentication middleware.

On every interactive update it ensures the Telegram user has a backend session:
it reuses a cached access token from Redis, or performs the Telegram auth
handshake with the backend and caches the fresh token. An authenticated
:class:`AsyncAPIClient` is then attached to the handler data as ``api`` and
closed once the handler returns.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as redis
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from bot.services.api_client import AsyncAPIClient

_TOKEN_PREFIX = "bot:token:"


class AuthMiddleware(BaseMiddleware):
    def __init__(
        self,
        backend_url: str,
        auth_secret: str,
        redis_client: redis.Redis,
        *,
        token_ttl: int,
        request_timeout: float,
    ) -> None:
        self._backend_url = backend_url
        self._auth_secret = auth_secret
        self._redis = redis_client
        self._token_ttl = token_ttl
        self._timeout = request_timeout

    @staticmethod
    def _key(user_id: int) -> str:
        return f"{_TOKEN_PREFIX}{user_id}"

    async def _resolve_token(self, user: User) -> str:
        cached = await self._redis.get(self._key(user.id))
        if cached:
            return cached if isinstance(cached, str) else cached.decode()

        async with AsyncAPIClient(
            self._backend_url,
            auth_secret=self._auth_secret,
            timeout=self._timeout,
        ) as anon:
            tokens = await anon.register_telegram_user(
                user.id, user.username, user.full_name
            )
        access_token: str = tokens["access_token"]
        await self._redis.set(self._key(user.id), access_token, ex=self._token_ttl)
        return access_token

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None or user.is_bot:
            return await handler(event, data)

        token = await self._resolve_token(user)
        api = AsyncAPIClient(
            self._backend_url, token=token, timeout=self._timeout
        )
        data["api"] = api
        try:
            return await handler(event, data)
        finally:
            await api.aclose()
