"""Order HTTP endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    DbSession,
    RedisClient,
    require_admin,
)
from src.core.pagination import Page, PaginationParams
from src.modules.orders.schemas import (
    OrderCreateRequest,
    OrderDetailResponse,
    OrderResponse,
    OrderStatusUpdateRequest,
)
from src.modules.orders.service import OrderService

router = APIRouter()


@router.post(
    "",
    response_model=OrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    data: OrderCreateRequest,
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> OrderDetailResponse:
    order = await OrderService(db, redis_client).create_from_cart(
        user.id, data  # type: ignore[attr-defined]
    )
    return OrderDetailResponse.model_validate(order)


@router.get("", response_model=Page[OrderResponse])
async def list_my_orders(
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
    params: Annotated[PaginationParams, Depends()],
) -> Page[OrderResponse]:
    page = await OrderService(db, redis_client).list_for_user(
        user.id, params  # type: ignore[attr-defined]
    )
    return page.map(OrderResponse.model_validate)


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_my_order(
    order_id: uuid.UUID,
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> OrderDetailResponse:
    order = await OrderService(db, redis_client).get_for_user(
        order_id, user.id  # type: ignore[attr-defined]
    )
    return OrderDetailResponse.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderDetailResponse)
async def cancel_my_order(
    order_id: uuid.UUID,
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> OrderDetailResponse:
    order = await OrderService(db, redis_client).cancel(
        order_id, user_id=user.id, role=user.role  # type: ignore[attr-defined]
    )
    return OrderDetailResponse.model_validate(order)


# --- Admin ------------------------------------------------------------------
@router.get(
    "/admin/all",
    response_model=Page[OrderResponse],
    dependencies=[Depends(require_admin)],
)
async def list_all_orders(
    db: DbSession,
    redis_client: RedisClient,
    params: Annotated[PaginationParams, Depends()],
) -> Page[OrderResponse]:
    page = await OrderService(db, redis_client).list_all(params)
    return page.map(OrderResponse.model_validate)


@router.patch(
    "/{order_id}/status",
    response_model=OrderDetailResponse,
    dependencies=[Depends(require_admin)],
)
async def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdateRequest,
    db: DbSession,
    redis_client: RedisClient,
) -> OrderDetailResponse:
    order = await OrderService(db, redis_client).transition(order_id, data.status)
    return OrderDetailResponse.model_validate(order)
