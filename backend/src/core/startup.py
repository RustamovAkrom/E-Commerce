"""Application startup helpers."""

from __future__ import annotations

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.security import hash_password
from src.modules.users.models import User

logger = structlog.get_logger()


async def create_superadmin(session: AsyncSession) -> None:
    """Create a superadmin user if one does not already exist.

    Credentials are read from ``settings`` (env vars).  If a user with
    ``ADMIN_EMAIL`` is already present the function returns silently.
    """
    existing = await session.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    )
    user = existing.scalar_one_or_none()

    if user:
        logger.info("superadmin_exists", email=settings.ADMIN_EMAIL)
        return

    user = User(
        email=settings.ADMIN_EMAIL,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        full_name=settings.ADMIN_FULL_NAME,
        role="SUPERADMIN",
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
