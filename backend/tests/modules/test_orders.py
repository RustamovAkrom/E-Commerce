"""Order endpoint tests: checkout from cart, status transitions, listing."""

from __future__ import annotations

from decimal import Decimal

import fakeredis.aioredis
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.users.models import User

from tests.factories import OrderFactory, ProductFactory

ORDERS = "/api/v1/orders"

_SHIPPING = {
    "full_name": "John Doe",
    "phone": "+998901112233",
    "address": "12 Main Street",
    "city": "Tashkent",
}


async def test_create_order_from_cart(
    client: AsyncClient,
    db_session: AsyncSession,
    redis_client: fakeredis.aioredis.FakeRedis,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(
        db_session, price=Decimal("50.00"), stock=10
    )
    # Seed the user's Redis cart with 2 units of the product.
    await redis_client.hset(f"cart:{customer_user.id}", str(product.id), 2)

    resp = await client.post(
        ORDERS, json={"shipping_address": _SHIPPING}, headers=auth_headers
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert Decimal(body["total_amount"]) == Decimal("100.00")
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 2

    # The cart is consumed once the order is staged.
    assert await redis_client.hgetall(f"cart:{customer_user.id}") == {}


async def test_order_status_transition(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    admin_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(db_session, stock=10)
    order = await OrderFactory.create(
        db_session,
        user=customer_user,
        items=[{"product": product, "quantity": 1}],
    )

    # The state machine forbids PENDING -> PROCESSING directly; PROCESSING is
    # reachable only via PAID. Drive the legal path PENDING -> PAID -> PROCESSING.
    to_paid = await client.patch(
        f"{ORDERS}/{order.id}/status",
        json={"status": "paid"},
        headers=admin_headers,
    )
    assert to_paid.status_code == 200, to_paid.text
    assert to_paid.json()["status"] == "paid"

    to_processing = await client.patch(
        f"{ORDERS}/{order.id}/status",
        json={"status": "processing"},
        headers=admin_headers,
    )
    assert to_processing.status_code == 200, to_processing.text
    assert to_processing.json()["status"] == "processing"


async def test_order_invalid_transition_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    admin_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(db_session, stock=10)
    order = await OrderFactory.create(
        db_session,
        user=customer_user,
        items=[{"product": product, "quantity": 1}],
    )
    # PENDING -> PROCESSING is illegal and must be rejected with a conflict.
    resp = await client.patch(
        f"{ORDERS}/{order.id}/status",
        json={"status": "processing"},
        headers=admin_headers,
    )
    assert resp.status_code == 409, resp.text


async def test_get_user_orders(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(db_session)
    await OrderFactory.create(
        db_session, user=customer_user, items=[{"product": product, "quantity": 1}]
    )
    await OrderFactory.create(
        db_session, user=customer_user, items=[{"product": product, "quantity": 2}]
    )

    resp = await client.get(ORDERS, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
