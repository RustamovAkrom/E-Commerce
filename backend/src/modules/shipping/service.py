"""Shipping business logic.

Three responsibilities:

* **Address book** — customers manage reusable destination addresses; at most
  one is flagged default.
* **Rate quotes** — delegate to the active carrier adapter for a price/ETA.
* **Shipments** — admin creates a shipment for a paid order (snapshotting the
  destination + assigning a tracking number via the carrier) and advances its
  delivery status.

The service owns persistence and carrier orchestration; carriers never touch
the database (see :mod:`src.modules.shipping.providers`).
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from src.core.pagination import Page, PaginationParams
from src.modules.orders.repository import OrderRepository
from src.modules.shipping.models import (
    Shipment,
    ShipmentStatus,
    ShippingAddress,
    ShippingMethod,
)
from src.modules.shipping.providers import RateQuote, get_carrier
from src.modules.shipping.repository import (
    ShipmentRepository,
    ShippingAddressRepository,
)
from src.modules.shipping.schemas import (
    RateQuoteRequest,
    ShipmentCreateRequest,
    ShippingAddressCreateRequest,
    ShippingAddressUpdateRequest,
)

# Delivery statuses that cannot transition further.
_TERMINAL_SHIPMENT_STATUSES = {
    ShipmentStatus.DELIVERED,
    ShipmentStatus.RETURNED,
    ShipmentStatus.CANCELLED,
}


class ShippingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.addresses = ShippingAddressRepository(session)
        self.shipments = ShipmentRepository(session)
        self.orders = OrderRepository(session)

    # --- Address book -------------------------------------------------------
    async def list_addresses(
        self, user_id: uuid.UUID
    ) -> list[ShippingAddress]:
        return await self.addresses.list_for_user(user_id)

    async def create_address(
        self, user_id: uuid.UUID, data: ShippingAddressCreateRequest
    ) -> ShippingAddress:
        if data.is_default:
            await self.addresses.clear_default(user_id)
        return await self.addresses.create(
            {"user_id": user_id, **data.model_dump()}
        )

    async def get_address(
        self, address_id: uuid.UUID, user_id: uuid.UUID
    ) -> ShippingAddress:
        address = await self.addresses.get(address_id)
        if address is None:
            raise NotFoundError("Address not found.")
        if address.user_id != user_id:
            raise PermissionDeniedError("This address does not belong to you.")
        return address

    async def update_address(
        self,
        address_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ShippingAddressUpdateRequest,
    ) -> ShippingAddress:
        address = await self.get_address(address_id, user_id)
        payload = data.model_dump(exclude_unset=True)
        if payload.get("is_default"):
            await self.addresses.clear_default(user_id)
        return await self.addresses.update(address, payload)

    async def delete_address(
        self, address_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        address = await self.get_address(address_id, user_id)
        await self.addresses.delete(address)

    # --- Rate quotes --------------------------------------------------------
    def quote(self, data: RateQuoteRequest) -> RateQuote:
        carrier = get_carrier()
        return carrier.quote(
            country=data.country, city=data.city, method=data.method
        )

    # --- Shipments ----------------------------------------------------------
    async def create_shipment(self, data: ShipmentCreateRequest) -> Shipment:
        order = await self.orders.get(data.order_id)
        if order is None:
            raise NotFoundError("Order not found.")

        existing = await self.shipments.get_for_order(order.id)
        if existing is not None and existing.status not in _TERMINAL_SHIPMENT_STATUSES:
            raise ConflictError("An active shipment already exists for this order.")

        destination = dict(order.shipping_address or {})
        country = str(destination.get("country", "UZ"))
        city = str(destination.get("city", ""))
        if not city:
            raise ValidationError("Order has no destination city to ship to.")

        carrier = get_carrier(data.carrier)
        quote = carrier.quote(
            country=country, city=city, method=data.method
        )
        draft = carrier.create_shipment(
            order_id=str(order.id),
            country=country,
            city=city,
            method=data.method,
        )

        shipment = Shipment(
            order_id=order.id,
            method=data.method,
            status=ShipmentStatus.LABEL_CREATED,
            carrier=draft.carrier,
            tracking_number=draft.tracking_number,
            cost=quote.cost,
            currency=quote.currency,
            destination=destination,
        )
        self.session.add(shipment)
        await self.session.flush()
        await self.session.refresh(shipment)
        return shipment

    async def get_shipment(self, shipment_id: uuid.UUID) -> Shipment:
        shipment = await self.shipments.get(shipment_id)
        if shipment is None:
            raise NotFoundError("Shipment not found.")
        return shipment

    async def get_for_order(self, order_id: uuid.UUID) -> Shipment:
        shipment = await self.shipments.get_for_order(order_id)
        if shipment is None:
            raise NotFoundError("No shipment for this order.")
        return shipment

    async def get_for_user_order(
        self, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Shipment:
        """Fetch the shipment of an order, asserting the order is the user's."""
        order = await self.orders.get(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        if order.user_id != user_id:
            raise PermissionDeniedError("This order does not belong to you.")
        return await self.get_for_order(order_id)

    async def list_shipments(self, params: PaginationParams) -> Page[Shipment]:
        items, total = await self.shipments.list_all(
            offset=params.offset, limit=params.limit
        )
        return Page.create(items, total, params)

    async def update_status(
        self, shipment_id: uuid.UUID, status: ShipmentStatus
    ) -> Shipment:
        shipment = await self.get_shipment(shipment_id)
        if shipment.status in _TERMINAL_SHIPMENT_STATUSES:
            raise ConflictError(
                "Shipment is in a final state and cannot change.",
                details={"status": shipment.status.value},
            )
        shipment.status = status
        self.session.add(shipment)
        await self.session.flush()
        await self.session.refresh(shipment)
        return shipment
