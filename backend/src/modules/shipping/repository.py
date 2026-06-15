"""Shipping repositories — DB queries only."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from src.core.base_repository import BaseRepository
from src.modules.shipping.models import Shipment, ShippingAddress


class ShippingAddressRepository(BaseRepository[ShippingAddress]):
    model = ShippingAddress

    async def list_for_user(self, user_id: uuid.UUID) -> list[ShippingAddress]:
        stmt = (
            select(ShippingAddress)
            .where(
                ShippingAddress.user_id == user_id,
                ShippingAddress.is_deleted.is_(False),
            )
            .order_by(
                ShippingAddress.is_default.desc(),
                ShippingAddress.created_at.desc(),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear_default(self, user_id: uuid.UUID) -> None:
        """Unset the default flag on every address owned by ``user_id``."""
        addresses = await self.list_for_user(user_id)
        for address in addresses:
            if address.is_default:
                address.is_default = False
                self.session.add(address)
        await self.session.flush()


class ShipmentRepository(BaseRepository[Shipment]):
    model = Shipment

    async def get_for_order(self, order_id: uuid.UUID) -> Shipment | None:
        stmt = (
            select(Shipment)
            .where(Shipment.order_id == order_id)
            .order_by(Shipment.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_all(
        self, *, offset: int, limit: int
    ) -> tuple[list[Shipment], int]:
        base = select(Shipment)
        total = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        stmt = base.order_by(Shipment.created_at.desc()).offset(offset).limit(limit)
        items = list((await self.session.execute(stmt)).scalars().all())
        return items, total
