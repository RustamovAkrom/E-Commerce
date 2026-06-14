"""Order repository — DB queries only."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.core.base_repository import BaseRepository
from src.modules.orders.models import Order


class OrderRepository(BaseRepository[Order]):
    model = Order

    async def get_with_items(self, order_id: uuid.UUID) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id, Order.is_deleted.is_(False))
            .options(selectinload(Order.items))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self, user_id: uuid.UUID, *, offset: int, limit: int
    ) -> tuple[list[Order], int]:
        base = select(Order).where(
            Order.user_id == user_id, Order.is_deleted.is_(False)
        )
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = (
            base.options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total

    async def list_all(
        self, *, offset: int, limit: int
    ) -> tuple[list[Order], int]:
        base = select(Order).where(Order.is_deleted.is_(False))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = (
            base.options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total
