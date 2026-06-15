"""Bot configuration loaded from environment variables.

Import the singleton ``settings`` rather than instantiating ``BotSettings``.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Strongly-typed bot configuration."""

    # --- Telegram -----------------------------------------------------------
    BOT_TOKEN: str = ""
    ADMIN_CHAT_ID: int = 0  # support messages are forwarded here

    # --- Backend ------------------------------------------------------------
    BACKEND_API_URL: str = "http://backend:8000"
    # Shared secret expected by the backend's POST /api/v1/auth/telegram.
    TELEGRAM_AUTH_SECRET: str = ""
    REQUEST_TIMEOUT: float = 15.0

    # --- Redis (FSM storage, auth-token cache, throttling) ------------------
    REDIS_URL: str = "redis://redis:6379/2"

    # --- Runtime mode -------------------------------------------------------
    # dev  -> long polling
    # prod -> webhook served by an aiohttp web server
    BOT_ENV: str = "dev"

    # --- Webhook (prod only) ------------------------------------------------
    WEBHOOK_BASE_URL: str = ""  # public https base, e.g. https://shop.example.com
    WEBHOOK_PATH: str = "/telegram/webhook"
    WEBHOOK_SECRET: str = ""  # X-Telegram-Bot-Api-Secret-Token value
    WEB_SERVER_HOST: str = "0.0.0.0"  # noqa: S104 -- container binds all interfaces
    WEB_SERVER_PORT: int = 8080

    # --- Throttling ---------------------------------------------------------
    THROTTLE_LIMIT: int = 30  # max requests ...
    THROTTLE_WINDOW: int = 60  # ... per this many seconds, per user

    # --- Auth-token cache ---------------------------------------------------
    # Access tokens live 15 min on the backend; cache slightly less.
    ACCESS_TOKEN_CACHE_TTL: int = 13 * 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def is_prod(self) -> bool:
        return self.BOT_ENV.strip().lower() in {"prod", "production"}

    @property
    def webhook_url(self) -> str:
        return f"{self.WEBHOOK_BASE_URL.rstrip('/')}{self.WEBHOOK_PATH}"


@lru_cache
def get_settings() -> BotSettings:
    return BotSettings()


settings = get_settings()
