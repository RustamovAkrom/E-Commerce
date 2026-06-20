"""Shared pytest fixtures.

Provides an isolated async database, a fake Redis, an HTTP client wired to the
real ``app`` with its DB/Redis dependencies overridden, and ready-made auth
headers for a CUSTOMER and an ADMIN user.

Tests use PostgreSQL (same as production) — no SQLite.
Database URL is read from ``TEST_DATABASE_URL`` env var, defaulting to
``postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce_test``.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from urllib.parse import quote

# Override system DEBUG=release (VS Code sets this) — tests need a boolean
os.environ.setdefault("DEBUG", "false")

import fakeredis.aioredis
import pytest_asyncio

# Importing the registry registers every ORM model on ``Base.metadata`` so that
# ``create_all`` builds the full schema.
import src.models_registry  # noqa: F401
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.config import settings
from src.core.database import Base
from src.core.dependencies import get_db, get_redis_client
from src.core.enums import UserRole
from src.core.rate_limit import limiter
from src.core.security import create_access_token
from src.main import app
from src.modules.users.models import User

# --- Test database URL (PostgreSQL) -----------------------------------------


def _postgres_url(database: str) -> str:
    return (
        f"postgresql+asyncpg://{quote(settings.DATABASE_USER)}:"
        f"{quote(settings.DATABASE_PASSWORD)}@"
        f"{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{database}"
    )


TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    _postgres_url("ecommerce_test"),
)
TEST_DB_ADMIN_URL = os.getenv(
    "TEST_DATABASE_ADMIN_URL",
    _postgres_url("postgres"),
)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> AsyncGenerator[asyncio.AbstractEventLoop, None]:
    """Create a single event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """Create the test database if it doesn't exist."""
    engine = create_async_engine(TEST_DB_ADMIN_URL, isolation_level="AUTOCOMMIT")
    try:
        async with engine.begin() as conn:
            # Check if test database exists
            result = await conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = 'ecommerce_test'")
            )
            if not result.scalar_one_or_none():
                await conn.execute(
                    text("CREATE DATABASE ecommerce_test")
                )
    finally:
        await engine.dispose()

    yield

    # Clean up test database after all tests
    async with engine.begin() as conn:
        try:
            await conn.execute(text("DROP DATABASE IF EXISTS ecommerce_test"))
        except Exception:
            pass


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """A fresh PostgreSQL engine for the test database."""
    eng = create_async_engine(TEST_DB_URL, future=True, pool_size=5)
    try:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Add username column if it doesn't exist
            result = await conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'username'
            """))
            if not result.scalar_one_or_none():
                await conn.execute(text("""
                    ALTER TABLE users
                    ADD COLUMN username VARCHAR(64) NOT NULL DEFAULT ''
                """))
                await conn.execute(text("""
                    UPDATE users
                    SET username = LOWER(SPLIT_PART(email, '@', 1))
                    WHERE username = ''
                """))
                await conn.execute(text("""
                    ALTER TABLE users
                    ADD CONSTRAINT users_username_key UNIQUE (username)
                """))
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture(autouse=True)
async def truncate_tables(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Truncate all tables before each test to ensure isolation."""
    yield
    tables = [
        "order_items", "payments", "reviews", "product_images",
        "product_attributes", "delivery_assignments", "shipments",
        "shipping_addresses", "stock_movements", "notifications",
        "order_status_history", "carts", "cart_items",
        "products", "vendors", "couriers", "categories", "users",
    ]
    async with engine.begin() as conn:
        for table in tables:
            try:
                await conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception:
                pass


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """A session for arranging test data directly (used by factories)."""
    maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with maker() as session:
        yield session
        # Clean up test data after each test
        try:
            await session.commit()
        except Exception:
            await session.rollback()


@pytest_asyncio.fixture
async def redis_client() -> AsyncGenerator[fakeredis.aioredis.FakeRedis, None]:
    """An in-process fake Redis matching the app's ``decode_responses=True``."""
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture
async def client(
    engine: AsyncEngine, redis_client: fakeredis.aioredis.FakeRedis
) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client bound to ``app`` with DB + Redis dependencies overridden."""
    maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def _override_get_redis() -> fakeredis.aioredis.FakeRedis:
        return redis_client

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_redis_client] = _override_get_redis
    limiter.enabled = False  # don't throttle the test client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    limiter.enabled = True


# --- Authenticated users / headers -----------------------------------------
def _bearer(user: User) -> dict[str, str]:
    token, _ = create_access_token(
        str(user.id), extra_claims={"role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def customer_user(db_session: AsyncSession) -> User:
    from tests.factories import UserFactory

    return await UserFactory.create(db_session, role=UserRole.CUSTOMER)


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    from tests.factories import UserFactory

    return await UserFactory.create(db_session, role=UserRole.ADMIN)


@pytest_asyncio.fixture
async def auth_headers(customer_user: User) -> dict[str, str]:
    """Bearer headers for a CUSTOMER-role user."""
    return _bearer(customer_user)


@pytest_asyncio.fixture
async def admin_headers(admin_user: User) -> dict[str, str]:
    """Bearer headers for an ADMIN-role user."""
    return _bearer(admin_user)
