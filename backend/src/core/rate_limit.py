"""Shared slowapi rate limiter, keyed by authenticated user or client IP."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _key_func(request: Request) -> str:
    """Prefer the authenticated user id; fall back to remote IP."""
    user = getattr(request.state, "user_id", None)
    if user:
        return f"user:{user}"
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func)
