"""Application startup helpers."""

from __future__ import annotations

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.enums import UserRole
from src.core.security import hash_password
from src.modules.users.models import User

logger = structlog.get_logger()


async def _table_exists(session: AsyncSession, table_name: str) -> bool:
    """Check if a table exists (works for both PostgreSQL and SQLite)."""
    try:
        result = await session.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_schema = 'public' AND table_name = :tbl"
                ")")
            .bindparams(tbl=table_name)
        )
        return bool(result.scalar_one())
    except Exception:
        # SQLite doesn't use information_schema.tables in the same way
        # Fall back to checking all_tables
        try:
            result = await session.execute(
                text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=:tbl"
                ).bindparams(tbl=table_name)
            )
            return result.scalar_one() is not None
        except Exception:
            return False


async def create_superadmin(session: AsyncSession) -> None:
    """Create a superadmin user if one does not already exist.

    Credentials are read from ``settings`` (env vars).  If a user with
    ``ADMIN_EMAIL`` is already present the function returns silently.
    """
    # Skip if tables don't exist yet (e.g. fresh DB, migrations not run)
    if not await _table_exists(session, "users"):
        logger.info("users_table_missing", msg="skipping superadmin creation")
        return

    existing = await session.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    )
    user = existing.scalar_one_or_none()

    if user:
        logger.info("superadmin_exists", email=settings.ADMIN_EMAIL)
        return

    user = User(
        email=settings.ADMIN_EMAIL.lower(),
        username=settings.ADMIN_EMAIL.split("@", 1)[0].lower(),
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        full_name=settings.ADMIN_FULL_NAME,
        role=UserRole.SUPERADMIN,
        is_active=True,
        is_verified=True,
    )
    session.add(user)
    try:
        await session.flush()
    except Exception:
        await session.rollback()
        # Re-check: another startup race may have committed already
        existing = await session.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        if existing.scalar_one_or_none():
            logger.info("superadmin_exists", email=settings.ADMIN_EMAIL)
            return
        raise
    logger.info(
        "superadmin_created",
        email=settings.ADMIN_EMAIL,
    )
