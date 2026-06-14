"""Async Redis connection pool and helpers.

A single shared pool is created lazily and reused across the app. Used for
the token blacklist, refresh-token store, cart storage and rate limiting.
"""

from __future__ import annotations

import redis.asyncio as redis

from src.config import settings

_pool: redis.ConnectionPool | None = None


def get_redis_pool() -> redis.ConnectionPool:
    """Return the shared connection pool, creating it on first use."""
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=50,
        )
    return _pool


def get_redis() -> redis.Redis:
    """Return a Redis client bound to the shared pool."""
    return redis.Redis(connection_pool=get_redis_pool())


async def close_redis() -> None:
    """Dispose of the pool on application shutdown."""
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
