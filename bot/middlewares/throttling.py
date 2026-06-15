"""Throttling middleware.

A fixed-window counter in Redis: at most ``limit`` updates per ``window``
seconds per user. When a user exceeds the limit the update is dropped and a
short "slow down" notice is shown.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as redis
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from bot.texts import THROTTLED

_THROTTLE_PREFIX = "bot:throttle:"


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(
        self, redis_client: redis.Redis, *, limit: int, window: int
    ) -> None:
        self._redis = redis_client
        self._limit = limit
        self._window = window

    @staticmethod
    def _key(user_id: int) -> str:
        return f"{_THROTTLE_PREFIX}{user_id}"

    async def _is_allowed(self, user_id: int) -> bool:
        key = self._key(user_id)
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, self._window)
        return count <= self._limit

    @staticmethod
    async def _notify(event: TelegramObject) -> None:
        if isinstance(event, Message):
            await event.answer(THROTTLED)
        elif isinstance(event, CallbackQuery):
            await event.answer(THROTTLED, show_alert=False)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        if not await self._is_allowed(user.id):
            await self._notify(event)
            return None
        return await handler(event, data)
