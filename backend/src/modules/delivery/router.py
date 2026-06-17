"""Delivery HTTP endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    DbSession,
    require_admin,
)
from src.core.pagination import Page, PaginationParams
from src.modules.delivery.schemas import (
    CourierCreateRequest,
    CourierResponse,
    CourierUpdateRequest,
    DeliveryAssignmentResponse,
)
from src.modules.delivery.service import DeliveryService

router = APIRouter()


# --- Admin: manage couriers -------------------------------------------------
@router.get(
    "/couriers",
    response_model=Page[CourierResponse],
    dependencies=[Depends(require_admin)],
)
async def list_couriers(
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
) -> Page[CourierResponse]:
    page = await DeliveryService(db).list_all(
        offset=params.offset, limit=params.limit
    )
    return page.map(CourierResponse.model_validate)


@router.post(
    "/couriers",
    response_model=CourierResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_courier(
    data: CourierCreateRequest,
    db: DbSession,
) -> CourierResponse:
    courier = await DeliveryService(db).create_courier(data)
    return CourierResponse.model_validate(courier)


@router.patch(
    "/couriers/{courier_id}",
    response_model=CourierResponse,
    dependencies=[Depends(require_admin)],
)
async def update_courier(
    courier_id: uuid.UUID,
    data: CourierUpdateRequest,
    db: DbSession,
) -> CourierResponse:
    courier = await DeliveryService(db).get_courier(courier_id)
    if courier is None:
        from src.core.exceptions import NotFoundError
        raise NotFoundError("Courier not found.")
    updated = await DeliveryService(db).update_courier(courier, data.model_dump(exclude_unset=True))
    return CourierResponse.model_validate(updated)


# --- Courier: own deliveries ------------------------------------------------
@router.get(
    "/courier/my-deliveries",
    response_model=list[DeliveryAssignmentResponse],
)
async def my_deliveries(
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> list[DeliveryAssignmentResponse]:
    """COURIER role: see pending deliveries assigned to them."""
    from src.modules.delivery.models import DeliveryStatus

    service = DeliveryService(db)
    courier = await service.get_by_user_id(user.id)  # type: ignore[attr-defined]
    if courier is None:
        return []
    assignments = await service.get_pending_for_courier(courier.id)
    return [
        DeliveryAssignmentResponse(
            id=a.id,
            order_id=a.order_id,
            courier_id=a.courier_id,
            courier_name=None,
            status=a.status.value,
            created_at=a.created_at,
        )
        for a in assignments
        if a.status != DeliveryStatus.DELIVERED
    ]


@router.post(
    "/courier/{assignment_id}/pickup",
    response_model=DeliveryAssignmentResponse,
)
async def pickup_delivery(
    assignment_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> DeliveryAssignmentResponse:
    """COURIER: mark a delivery as picked up."""

    service = DeliveryService(db)
    courier = await service.get_by_user_id(user.id)  # type: ignore[attr-defined]
    if courier is None:
        from src.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("You are not registered as a courier.")
    assignment = await service.pickup(courier.id, assignment_id)
    return DeliveryAssignmentResponse(
        id=assignment.id,
        order_id=assignment.order_id,
        courier_id=assignment.courier_id,
        courier_name=None,
        status=assignment.status.value,
        created_at=assignment.created_at,
    )


@router.post(
    "/courier/{assignment_id}/delivered",
    response_model=DeliveryAssignmentResponse,
)
async def mark_delivered(
    assignment_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> DeliveryAssignmentResponse:
    """COURIER: mark a delivery as delivered."""
    service = DeliveryService(db)
    courier = await service.get_by_user_id(user.id)  # type: ignore[attr-defined]
    if courier is None:
        from src.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("You are not registered as a courier.")
    assignment = await service.mark_delivered(courier.id, assignment_id)
    return DeliveryAssignmentResponse(
        id=assignment.id,
        order_id=assignment.order_id,
        courier_id=assignment.courier_id,
        courier_name=None,
        status=assignment.status.value,
        created_at=assignment.created_at,
    )
