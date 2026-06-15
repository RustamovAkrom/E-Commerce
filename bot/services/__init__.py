"""Service layer: the bot's only gateway to the backend (REST over httpx)."""

from __future__ import annotations

from bot.services.api_client import APIError, AsyncAPIClient

__all__ = ["APIError", "AsyncAPIClient"]
