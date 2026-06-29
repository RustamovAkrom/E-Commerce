"""Delivery repository."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.core.base_repository import BaseRepository
from src.modules.delivery.models import (
    Courier,
    DeliveryAssignment,
    DeliveryStatus,
)


class CourierRepository(BaseRepository[Courier]):
    model = Courier

    async def get_by_user_id(self, user_id: uuid.UUID) -> Courier | None:
        return await self.get_by(user_id=user_id)

    async def get_active_near_zone(
        self, zone: str | None, limit: int = 3
    ) -> list[Courier]:
        """Return available couriers, optionally filtered by zone."""
        stmt = select(Courier).where(
            Courier.is_deleted.is_(False),
            Courier.is_active.is_(True),
        )
        if zone:
            stmt = stmt.where(Courier.zone == zone)
        stmt = stmt.order_by(Courier.created_at).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class DeliveryAssignmentRepository(BaseRepository[DeliveryAssignment]):
    model = DeliveryAssignment

    async def get_pending_for_courier(
        self, courier_id: uuid.UUID
    ) -> list[DeliveryAssignment]:
        stmt = (
            select(DeliveryAssignment)
            .where(
                DeliveryAssignment.courier_id == courier_id,
                DeliveryAssignment.status == "pending",
            )
            .order_by(DeliveryAssignment.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_for_courier(
        self, courier_id: uuid.UUID
    ) -> list[DeliveryAssignment]:
        """Active (not-yet-delivered) deliveries with their order eager-loaded.

        Returns both PENDING and PICKED_UP so the courier sees work in progress;
        terminal states (delivered/failed/cancelled) are excluded.
        """
        stmt = (
            select(DeliveryAssignment)
            .where(
                DeliveryAssignment.courier_id == courier_id,
                DeliveryAssignment.status.in_(
                    [DeliveryStatus.PENDING, DeliveryStatus.PICKED_UP]
                ),
            )
            .options(selectinload(DeliveryAssignment.order))
            .order_by(DeliveryAssignment.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
