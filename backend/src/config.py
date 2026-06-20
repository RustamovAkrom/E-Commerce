"""Application settings loaded from environment variables.

Everything in the platform depends on this module. Import the singleton
``settings`` instance rather than instantiating ``Settings`` yourself.
"""

from __future__ import annotations

from functools import lru_cache

from urllib.parse import quote

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_bool(value: object) -> bool:
    """Coerce string values like 'release', 'true', '1' etc. to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.strip().lower()
        if low in ("true", "1", "yes", "on"):
            return True
        if low in ("false", "0", "no", "off"):
            return False
    return bool(value)


class Settings(BaseSettings):
    """Strongly-typed application configuration."""

    # --- Core ---------------------------------------------------------------
    APP_NAME: str = "ECommerce Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(min_length=32)
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # --- Feature flags ------------------------------------------------------
    ELASTICSEARCH_ENABLED: bool = False   # Toggle full-text search
    TELEGRAM_BOT_ENABLED: bool = True

    # --- JWT ----------------------------------------------------------------
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_TTL_SECONDS: int = 60 * 15            # 15 minutes
    REFRESH_TOKEN_TTL_SECONDS: int = 60 * 60 * 24 * 30  # 30 days

    # --- Database -----------------------------------------------------------
    DATABASE_HOST: str = "postgres"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "ecommerce"
    DATABASE_PASSWORD: str = "postgres"
    DATABASE_NAME: str = "ecommerce"
    DATABASE_ASYNC_DRIVER: str = "asyncpg"
    DATABASE_SYNC_DRIVER: str = "psycopg2"

    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # --- Redis --------------------------------------------------------------
    REDIS_URL: str = "redis://redis:6379/0"
    CART_TTL_SECONDS: int = 60 * 60 * 24 * 7  # carts live 7 days

    # --- RabbitMQ / Celery --------------------------------------------------
    CELERY_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672//"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # --- Storage (MinIO / S3) ----------------------------------------------
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "ecommerce"
    MINIO_SECURE: bool = False
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_UPLOAD_MIME: list[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    ]

    # --- Elasticsearch ------------------------------------------------------
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"

    # --- Payments -----------------------------------------------------------
    CLICK_SERVICE_ID: str = ""
    CLICK_MERCHANT_ID: str = ""
    CLICK_SECRET_KEY: str = ""
    PAYME_ID: str = ""
    PAYME_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # --- Notifications ------------------------------------------------------
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@example.com"
    SMTP_TLS: bool = True
    ESKIZ_EMAIL: str = ""
    ESKIZ_PASSWORD: str = ""
    ESKIZ_BASE_URL: str = "https://notify.eskiz.uz/api"

    # --- Telegram -----------------------------------------------------------
    BOT_TOKEN: str = ""
    BACKEND_API_URL: str = "http://backend:8000"
    TELEGRAM_AUTH_SECRET: str = ""  # shared secret for /auth/telegram

    # --- Rate limiting ------------------------------------------------------
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # --- Monitoring ---------------------------------------------------------
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    # --- Superadmin (auto-created on first startup) -------------------------
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme123"
    ADMIN_FULL_NAME: str = "Super Admin"

    # --- Tooling ------------------------------------------------------------
    # SQLAdmin database UI at /admin/db. Enabled in DEBUG mode or explicitly.
    SQLADMIN_ENABLED: bool = False

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        """Coerce string values like 'release', 'true', '1' to bool."""
        return _parse_bool(value)

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.backend"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @property
    def DATABASE_URL(self) -> str:
        if self.is_sqlite:
            return f"sqlite+aiosqlite:///{self.DATABASE_NAME}"
        return (
            f"postgresql+{self.DATABASE_ASYNC_DRIVER}://{quote(self.DATABASE_USER)}:{quote(self.DATABASE_PASSWORD)}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        if self.is_sqlite:
            return f"sqlite+{self.DATABASE_SYNC_DRIVER}:///{self.DATABASE_NAME}"
        return (
            f"postgresql+{self.DATABASE_SYNC_DRIVER}://{quote(self.DATABASE_USER)}:{quote(self.DATABASE_PASSWORD)}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_NAME.endswith(".db")


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (used by dependency injection / tests)."""
    return Settings()  # type: ignore[call-arg]  # values sourced from env


settings = get_settings()
