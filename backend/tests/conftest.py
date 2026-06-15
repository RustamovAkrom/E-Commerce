"""Shared pytest fixtures.

Provides an isolated async database, a fake Redis, an HTTP client wired to the
real ``app`` with its DB/Redis dependencies overridden, and ready-made auth
headers for a CUSTOMER and an ADMIN user.

Each test gets a fresh file-backed SQLite database. A file (rather than a
shared-memory) database is used deliberately: the application opens a new
connection/session per request, and a file database lets those connections see
each other's committed writes without the single-connection contention of an
in-memory ``StaticPool``.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncGenerator

import fakeredis.aioredis
import pytest_asyncio

# Importing the registry registers every ORM model on ``Base.metadata`` so that
# ``create_all`` builds the full schema.
import src.models_registry  # noqa: F401
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.core.database import Base
from src.core.dependencies import get_db, get_redis_client
from src.core.enums import UserRole
from src.core.rate_limit import limiter
from src.core.security import create_access_token
from src.main import app
from src.modules.users.models import User


@pytest_asyncio.fixture
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    """A fresh, schema-loaded SQLite database per test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite+aiosqlite:///{path.replace(os.sep, '/')}"
    eng = create_async_engine(url, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()
        try:
            os.unlink(path)
        except OSError:
            # On Windows the file may linger briefly after dispose; harmless.
            pass


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """A session for arranging test data directly (used by factories)."""
    maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with maker() as session:
        yield session


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
