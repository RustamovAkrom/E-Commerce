"""Cart HTTP endpoints (authenticated)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from src.core.dependencies import CurrentUser, DbSession, RedisClient
from src.core.schemas import MessageResponse
from src.modules.cart.schemas import CartItemRequest, CartResponse
from src.modules.cart.service import CartService

router = APIRouter()


@router.get("", response_model=CartResponse)
async def get_cart(
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> CartResponse:
    return await CartService(db, redis_client).get_cart(user.id)  # type: ignore[attr-defined]


@router.post("/items", response_model=CartResponse)
async def add_item(
    data: CartItemRequest,
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> CartResponse:
    return await CartService(db, redis_client).add_item(
        user.id, data.product_id, data.quantity  # type: ignore[attr-defined]
    )


@router.put("/items", response_model=CartResponse)
async def set_item(
    data: CartItemRequest,
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> CartResponse:
    return await CartService(db, redis_client).set_item(
        user.id, data.product_id, data.quantity  # type: ignore[attr-defined]
    )


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_item(
    product_id: uuid.UUID,
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> CartResponse:
    return await CartService(db, redis_client).remove_item(
        user.id, product_id  # type: ignore[attr-defined]
    )


@router.delete("", response_model=MessageResponse)
async def clear_cart(
    db: DbSession,
    redis_client: RedisClient,
    user: CurrentUser,  # type: ignore[valid-type]
) -> MessageResponse:
    await CartService(db, redis_client).clear(user.id)  # type: ignore[attr-defined]
    return MessageResponse(message="Cart cleared.")
