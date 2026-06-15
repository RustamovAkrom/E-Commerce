"""Notification repository — DB queries only."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from src.core.base_repository import BaseRepository
from src.modules.notifications.models import Notification


class NotificationRepository(BaseRepository[Notification]):
    model = Notification

    async def list_for_user(
        self, user_id: uuid.UUID, *, offset: int, limit: int
    ) -> tuple[list[Notification], int]:
        base = select(Notification).where(Notification.user_id == user_id)
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = (
            base.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total
