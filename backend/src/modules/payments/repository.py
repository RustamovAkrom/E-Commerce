"""Payment repository — DB queries only."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from src.core.base_repository import BaseRepository
from src.core.enums import PaymentProvider
from src.modules.payments.models import Payment


class PaymentRepository(BaseRepository[Payment]):
    model = Payment

    async def get_by_provider_txn(
        self, provider: PaymentProvider, provider_payment_id: str
    ) -> Payment | None:
        stmt = select(Payment).where(
            Payment.provider == provider,
            Payment.provider_payment_id == provider_payment_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_order(self, order_id: uuid.UUID) -> list[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.order_id == order_id)
            .order_by(Payment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_user(
        self, user_id: uuid.UUID, *, offset: int, limit: int
    ) -> tuple[list[Payment], int]:
        base = select(Payment).where(Payment.user_id == user_id)
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = base.order_by(Payment.created_at.desc()).offset(offset).limit(limit)
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total
