"""Shipping HTTP endpoints.

Customer-facing: manage the personal address book, request rate quotes, and
read the shipment for one of their own orders. Admin-facing: create shipments
for orders and advance delivery status.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import CurrentUser, DbSession, require_admin
from src.core.pagination import Page, PaginationParams
from src.core.schemas import MessageResponse
from src.modules.shipping.schemas import (
    RateQuoteRequest,
    RateQuoteResponse,
    ShipmentCreateRequest,
    ShipmentResponse,
    ShipmentStatusUpdateRequest,
    ShippingAddressCreateRequest,
    ShippingAddressResponse,
    ShippingAddressUpdateRequest,
)
from src.modules.shipping.service import ShippingService

router = APIRouter()


# --- Address book -----------------------------------------------------------
@router.get("/addresses", response_model=list[ShippingAddressResponse])
async def list_addresses(
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> list[ShippingAddressResponse]:
    addresses = await ShippingService(db).list_addresses(user.id)  # type: ignore[attr-defined]
    return [ShippingAddressResponse.model_validate(a) for a in addresses]


@router.post(
    "/addresses",
    response_model=ShippingAddressResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_address(
    data: ShippingAddressCreateRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> ShippingAddressResponse:
    address = await ShippingService(db).create_address(user.id, data)  # type: ignore[attr-defined]
    return ShippingAddressResponse.model_validate(address)


@router.patch(
    "/addresses/{address_id}", response_model=ShippingAddressResponse
)
async def update_address(
    address_id: uuid.UUID,
    data: ShippingAddressUpdateRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> ShippingAddressResponse:
    address = await ShippingService(db).update_address(
        address_id, user.id, data  # type: ignore[attr-defined]
    )
    return ShippingAddressResponse.model_validate(address)


@router.delete(
    "/addresses/{address_id}", response_model=MessageResponse
)
async def delete_address(
    address_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> MessageResponse:
    await ShippingService(db).delete_address(address_id, user.id)  # type: ignore[attr-defined]
    return MessageResponse(message="Address deleted.")


# --- Rate quotes ------------------------------------------------------------
@router.post("/quote", response_model=RateQuoteResponse)
async def quote_rate(
    data: RateQuoteRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> RateQuoteResponse:
    quote = ShippingService(db).quote(data)
    return RateQuoteResponse(
        method=quote.method,
        carrier=quote.carrier,
        cost=quote.cost,
        currency=quote.currency,
        eta_days=quote.eta_days,
    )


# --- Shipment (customer view) ----------------------------------------------
@router.get("/orders/{order_id}/shipment", response_model=ShipmentResponse)
async def get_order_shipment(
    order_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> ShipmentResponse:
    shipment = await ShippingService(db).get_for_user_order(
        order_id, user.id  # type: ignore[attr-defined]
    )
    return ShipmentResponse.model_validate(shipment)


# --- Shipments (admin) ------------------------------------------------------
@router.post(
    "/shipments",
    response_model=ShipmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_shipment(
    data: ShipmentCreateRequest,
    db: DbSession,
) -> ShipmentResponse:
    shipment = await ShippingService(db).create_shipment(data)
    return ShipmentResponse.model_validate(shipment)


@router.get(
    "/shipments",
    response_model=Page[ShipmentResponse],
    dependencies=[Depends(require_admin)],
)
async def list_shipments(
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
) -> Page[ShipmentResponse]:
    page = await ShippingService(db).list_shipments(params)
    return page.map(ShipmentResponse.model_validate)


@router.get(
    "/shipments/{shipment_id}",
    response_model=ShipmentResponse,
    dependencies=[Depends(require_admin)],
)
async def get_shipment(
    shipment_id: uuid.UUID,
    db: DbSession,
) -> ShipmentResponse:
    shipment = await ShippingService(db).get_shipment(shipment_id)
    return ShipmentResponse.model_validate(shipment)


@router.patch(
    "/shipments/{shipment_id}/status",
    response_model=ShipmentResponse,
    dependencies=[Depends(require_admin)],
)
async def update_shipment_status(
    shipment_id: uuid.UUID,
    data: ShipmentStatusUpdateRequest,
    db: DbSession,
) -> ShipmentResponse:
    shipment = await ShippingService(db).update_status(shipment_id, data.status)
    return ShipmentResponse.model_validate(shipment)
