"""Vendor repository — DB queries only."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from src.core.base_repository import BaseRepository
from src.modules.vendors.models import Vendor, VendorStatus


class VendorRepository(BaseRepository[Vendor]):
    model = Vendor

    async def get_by_slug(self, slug: str) -> Vendor | None:
        return await self.get_by(slug=slug)

    async def get_by_user(self, user_id: uuid.UUID) -> Vendor | None:
        return await self.get_by(user_id=user_id)

    async def list_public(
        self, *, offset: int, limit: int
    ) -> tuple[list[Vendor], int]:
        """Approved, active vendors for the public storefront."""
        base = select(Vendor).where(
            Vendor.is_deleted.is_(False),
            Vendor.is_active.is_(True),
            Vendor.status == VendorStatus.APPROVED,
        )
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = base.order_by(Vendor.name).offset(offset).limit(limit)
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total

    async def list_all(
        self, *, offset: int, limit: int
    ) -> tuple[list[Vendor], int]:
        base = select(Vendor).where(Vendor.is_deleted.is_(False))
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = base.order_by(Vendor.created_at.desc()).offset(offset).limit(limit)
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total
