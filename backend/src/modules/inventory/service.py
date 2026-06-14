"""Inventory business logic — stock adjustments and reservations.

Stock is mutated atomically with a guarded UPDATE so concurrent orders cannot
drive stock negative. Every change writes a :class:`StockMovement` ledger row.
"""

from __future__ import annotations

import uuid

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.modules.catalog.models import Product
from src.modules.inventory.models import MovementReason, StockMovement
from src.modules.inventory.schemas import StockAdjustRequest


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _record_movement(
        self,
        product_id: uuid.UUID,
        delta: int,
        reason: MovementReason,
        reference: str | None,
    ) -> StockMovement:
        movement = StockMovement(
            product_id=product_id,
            delta=delta,
            reason=reason,
            reference=reference,
        )
        self.session.add(movement)
        await self.session.flush()
        return movement

    async def adjust(self, data: StockAdjustRequest) -> int:
        """Apply a manual stock delta, returning the new stock level."""
        product = await self.session.get(Product, data.product_id)
        if product is None or product.is_deleted:
            raise NotFoundError("Product not found.")
        new_stock = product.stock + data.delta
        if new_stock < 0:
            raise ValidationError("Adjustment would result in negative stock.")
        product.stock = new_stock
        self.session.add(product)
        await self._record_movement(
            data.product_id, data.delta, data.reason, data.reference
        )
        await self.session.flush()
        return new_stock

    async def reserve(
        self, product_id: uuid.UUID, quantity: int, reference: str | None = None
    ) -> None:
        """Atomically decrement stock for an order; raise if insufficient.

        Uses a conditional UPDATE (``stock >= quantity``) so two concurrent
        orders cannot both succeed against the same last unit.
        """
        if quantity <= 0:
            raise ValidationError("Reservation quantity must be positive.")
        stmt = (
            update(Product)
            .where(
                Product.id == product_id,
                Product.is_deleted.is_(False),
                Product.stock >= quantity,
            )
            .values(stock=Product.stock - quantity)
        )
        result = await self.session.execute(stmt)
        if result.rowcount == 0:
            raise ConflictError(
                "Insufficient stock to reserve.",
                details={"product_id": str(product_id), "quantity": quantity},
            )
        await self._record_movement(
            product_id, -quantity, MovementReason.RESERVATION, reference
        )

    async def release(
        self, product_id: uuid.UUID, quantity: int, reference: str | None = None
    ) -> None:
        """Return previously reserved stock (e.g. on cancellation)."""
        if quantity <= 0:
            raise ValidationError("Release quantity must be positive.")
        stmt = (
            update(Product)
            .where(Product.id == product_id)
            .values(stock=Product.stock + quantity)
        )
        await self.session.execute(stmt)
        await self._record_movement(
            product_id, quantity, MovementReason.RELEASE, reference
        )

    async def get_level(self, product_id: uuid.UUID) -> int:
        product = await self.session.get(Product, product_id)
        if product is None or product.is_deleted:
            raise NotFoundError("Product not found.")
        return product.stock
