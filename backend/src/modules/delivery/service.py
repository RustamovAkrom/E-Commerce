"""Delivery service — courier management and assignment."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.delivery.models import Courier, DeliveryAssignment, DeliveryStatus
from src.modules.delivery.repository import (
    CourierRepository,
    DeliveryAssignmentRepository,
)
from src.modules.delivery.schemas import CourierCreateRequest


class DeliveryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.couriers = CourierRepository(session)
        self.assignments = DeliveryAssignmentRepository(session)

    async def get_courier(self, courier_id: uuid.UUID) -> Courier | None:
        return await self.couriers.get(courier_id)

    async def get_by_user_id(self, user_id: uuid.UUID) -> Courier | None:
        return await self.couriers.get_by_user_id(user_id)

    async def list_all(
        self, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Courier], int]:
        items = await self.couriers.get_many(offset=offset, limit=limit)
        total = await self.couriers.count()
        return items, total

    async def create_courier(
        self, data: CourierCreateRequest
    ) -> Courier:
        """Create a courier account linked to an existing user."""
        courier = await self.couriers.create(
            {
                "user_id": data.user_id,
                "phone": data.phone,
                "zone": data.zone,
            }
        )
        return courier

    async def update_courier(
        self, courier: Courier, data: dict
    ) -> Courier:
        return await self.couriers.update(courier, data)

    async def get_pending_for_courier(
        self, courier_id: uuid.UUID
    ) -> list[DeliveryAssignment]:
        return await self.assignments.get_pending_for_courier(courier_id)

    async def assign_nearest_courier(
        self, order_id: uuid.UUID, zone: str | None
    ) -> Courier | None:
        """Auto-assign the nearest available courier to an order."""
        available = await self.couriers.get_active_near_zone(zone)
        if not available:
            return None
        courier = available[0]
        assignment = DeliveryAssignment(
            order_id=order_id,
            courier_id=courier.id,
            status=DeliveryStatus.PENDING,
        )
        self.session.add(assignment)
        await self.session.flush()
        return courier

    async def pickup(self, courier_id: uuid.UUID, assignment_id: uuid.UUID) -> DeliveryAssignment:
        """Mark a delivery as picked up by a courier."""
        assignment = await self.assignments.get(assignment_id)
        if assignment is None or assignment.courier_id != courier_id:
            raise ValueError("Assignment not found or not yours.")
        assignment.status = DeliveryStatus.PICKED_UP
        await self.session.flush()
        return assignment

    async def mark_delivered(
        self, courier_id: uuid.UUID, assignment_id: uuid.UUID
    ) -> DeliveryAssignment:
        """Mark a delivery as successfully delivered."""
        assignment = await self.assignments.get(assignment_id)
        if assignment is None or assignment.courier_id != courier_id:
            raise ValueError("Assignment not found or not yours.")
        assignment.status = DeliveryStatus.DELIVERED
        await self.session.flush()
        return assignment
