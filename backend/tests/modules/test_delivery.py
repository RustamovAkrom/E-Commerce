"""Delivery endpoint tests: courier management and the courier pickup flow."""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.enums import UserRole
from src.core.security import create_access_token
from src.modules.delivery.models import (
    Courier,
    DeliveryAssignment,
    DeliveryStatus,
)
from src.modules.users.models import User

from tests.factories import OrderFactory, ProductFactory, UserFactory

DELIVERY = "/api/v1/delivery"


def _courier_headers(user: User) -> dict[str, str]:
    token, _ = create_access_token(
        str(user.id), extra_claims={"role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


async def _make_courier(
    session: AsyncSession,
    *,
    user: User,
    zone: str | None = "Tashkent-Center",
) -> Courier:
    courier = Courier(user_id=user.id, phone="+998901112233", zone=zone)
    session.add(courier)
    await session.commit()
    await session.refresh(courier)
    return courier


async def _make_assignment(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    courier_id: uuid.UUID | None,
    status: DeliveryStatus = DeliveryStatus.PENDING,
) -> DeliveryAssignment:
    assignment = DeliveryAssignment(
        order_id=order_id,
        courier_id=courier_id,
        status=status,
    )
    session.add(assignment)
    await session.commit()
    await session.refresh(assignment)
    return assignment


async def test_list_couriers_as_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
) -> None:
    """REGRESSION: listing couriers used to 500; it must return a page."""
    courier_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    await _make_courier(db_session, user=courier_user)

    resp = await client.get(f"{DELIVERY}/couriers", headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1


async def test_create_courier_as_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
) -> None:
    courier_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    resp = await client.post(
        f"{DELIVERY}/couriers",
        json={
            "user_id": str(courier_user.id),
            "phone": "+998901112233",
            "zone": "Tashkent-Center",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user_id"] == str(courier_user.id)
    assert body["zone"] == "Tashkent-Center"


async def test_courier_pickup_flow(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    courier_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    courier = await _make_courier(db_session, user=courier_user)

    product = await ProductFactory.create(db_session, stock=10)
    order = await OrderFactory.create(
        db_session, user=courier_user, items=[{"product": product, "quantity": 1}]
    )
    assignment = await _make_assignment(
        db_session, order_id=order.id, courier_id=courier.id
    )

    resp = await client.post(
        f"{DELIVERY}/courier/{assignment.id}/pickup",
        headers=_courier_headers(courier_user),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == DeliveryStatus.PICKED_UP.value


async def test_pickup_nonexistent_assignment_returns_404(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """REGRESSION: an unknown assignment id must be 404, never a 500."""
    courier_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    await _make_courier(db_session, user=courier_user)

    resp = await client.post(
        f"{DELIVERY}/courier/{uuid.uuid4()}/pickup",
        headers=_courier_headers(courier_user),
    )
    assert resp.status_code == 404, resp.text


async def test_pickup_other_couriers_assignment_forbidden(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """REGRESSION: picking up another courier's delivery must be 403."""
    owner_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    owner = await _make_courier(db_session, user=owner_user)

    other_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    await _make_courier(db_session, user=other_user, zone="Samarkand")

    product = await ProductFactory.create(db_session, stock=10)
    order = await OrderFactory.create(
        db_session, user=owner_user, items=[{"product": product, "quantity": 1}]
    )
    assignment = await _make_assignment(
        db_session, order_id=order.id, courier_id=owner.id
    )

    resp = await client.post(
        f"{DELIVERY}/courier/{assignment.id}/pickup",
        headers=_courier_headers(other_user),
    )
    assert resp.status_code == 403, resp.text


async def test_delivered_before_pickup_conflicts(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """REGRESSION (transition guard): a PENDING delivery cannot be delivered."""
    courier_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    courier = await _make_courier(db_session, user=courier_user)

    product = await ProductFactory.create(db_session, stock=10)
    order = await OrderFactory.create(
        db_session, user=courier_user, items=[{"product": product, "quantity": 1}]
    )
    assignment = await _make_assignment(
        db_session, order_id=order.id, courier_id=courier.id
    )

    resp = await client.post(
        f"{DELIVERY}/courier/{assignment.id}/delivered",
        headers=_courier_headers(courier_user),
    )
    assert resp.status_code == 409, resp.text


async def test_double_pickup_conflicts(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """REGRESSION (transition guard): picking up an already-picked-up delivery
    must be a 409, not a silent re-transition."""
    courier_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    courier = await _make_courier(db_session, user=courier_user)

    product = await ProductFactory.create(db_session, stock=10)
    order = await OrderFactory.create(
        db_session, user=courier_user, items=[{"product": product, "quantity": 1}]
    )
    assignment = await _make_assignment(
        db_session,
        order_id=order.id,
        courier_id=courier.id,
        status=DeliveryStatus.PICKED_UP,
    )

    resp = await client.post(
        f"{DELIVERY}/courier/{assignment.id}/pickup",
        headers=_courier_headers(courier_user),
    )
    assert resp.status_code == 409, resp.text


async def test_my_deliveries_returns_pending_assignments(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    courier_user = await UserFactory.create(db_session, role=UserRole.COURIER)
    courier = await _make_courier(db_session, user=courier_user)

    product = await ProductFactory.create(db_session, stock=10)
    order = await OrderFactory.create(
        db_session, user=courier_user, items=[{"product": product, "quantity": 1}]
    )
    assignment = await _make_assignment(
        db_session, order_id=order.id, courier_id=courier.id
    )

    resp = await client.get(
        f"{DELIVERY}/courier/my-deliveries",
        headers=_courier_headers(courier_user),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["id"] == str(assignment.id)
    assert body[0]["status"] == DeliveryStatus.PENDING.value
