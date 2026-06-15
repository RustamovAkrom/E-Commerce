"""Review repository — DB queries only."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from src.core.base_repository import BaseRepository
from src.modules.reviews.models import Review


class ReviewRepository(BaseRepository[Review]):
    model = Review

    async def get_user_review(
        self, product_id: uuid.UUID, user_id: uuid.UUID
    ) -> Review | None:
        stmt = select(Review).where(
            Review.product_id == product_id,
            Review.user_id == user_id,
            Review.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_product(
        self,
        product_id: uuid.UUID,
        *,
        offset: int,
        limit: int,
        approved_only: bool = True,
    ) -> tuple[list[Review], int]:
        base = select(Review).where(
            Review.product_id == product_id,
            Review.is_deleted.is_(False),
        )
        if approved_only:
            base = base.where(Review.is_approved.is_(True))

        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = base.order_by(Review.created_at.desc()).offset(offset).limit(limit)
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total

    async def list_all(
        self, *, offset: int, limit: int
    ) -> tuple[list[Review], int]:
        base = select(Review).where(Review.is_deleted.is_(False))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = base.order_by(Review.created_at.desc()).offset(offset).limit(limit)
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total

    async def rating_summary(
        self, product_id: uuid.UUID
    ) -> tuple[float, int]:
        """Return ``(average_rating, count)`` over approved reviews."""
        stmt = select(
            func.coalesce(func.avg(Review.rating), 0.0),
            func.count(Review.id),
        ).where(
            Review.product_id == product_id,
            Review.is_deleted.is_(False),
            Review.is_approved.is_(True),
        )
        avg, count = (await self.session.execute(stmt)).one()
        return float(avg), int(count)
