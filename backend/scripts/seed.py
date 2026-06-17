"""Seed script for creating initial platform users.

Run: ``uv run python -m scripts.seed``
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from src.core.database import async_session_maker
from src.core.enums import UserRole
from src.core.security import hash_password
from src.modules.users.models import User

OPERATOR_EMAIL = "operator@test.com"
OPERATOR_PASSWORD = "operator123"
OPERATOR_FULL_NAME = "Platform Operator"


async def seed_operator() -> None:
    """Create an OPERATOR user if it doesn't exist."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == OPERATOR_EMAIL)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[SKIP] Operator {OPERATOR_EMAIL} already exists (id={existing.id})")
            return

        operator = User(
            email=OPERATOR_EMAIL,
            hashed_password=hash_password(OPERATOR_PASSWORD),
            full_name=OPERATOR_FULL_NAME,
            role=UserRole.OPERATOR,
            is_active=True,
            is_verified=True,
        )
        session.add(operator)
        await session.flush()
        await session.refresh(operator)
        print(f"[OK] Created OPERATOR user: {OPERATOR_EMAIL} (id={operator.id})")
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_operator())
