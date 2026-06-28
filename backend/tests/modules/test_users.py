"""User endpoint tests: profile, password change, admin listing, role guards."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.enums import UserRole
from src.modules.users.models import User

from tests.factories import UserFactory

USERS = "/api/v1/users"


async def test_read_me_returns_current_user(
    client: AsyncClient,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    resp = await client.get(f"{USERS}/me", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == str(customer_user.id)
    assert body["email"] == customer_user.email
    assert body["role"] == UserRole.CUSTOMER.value


async def test_update_me_updates_profile(
    client: AsyncClient,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    resp = await client.patch(
        f"{USERS}/me",
        json={"full_name": "New Name", "phone": "+998901234567"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["full_name"] == "New Name"
    assert body["phone"] == "+998901234567"


async def test_change_password_with_correct_current(
    client: AsyncClient,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    # ``customer_user`` is seeded with the factory default password.
    resp = await client.post(
        f"{USERS}/me/password",
        json={"current_password": "password123", "new_password": "newpassword456"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text


async def test_change_password_with_wrong_current_rejected(
    client: AsyncClient,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    resp = await client.post(
        f"{USERS}/me/password",
        json={"current_password": "wrongpassword", "new_password": "newpassword456"},
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text


async def test_list_users_as_admin(
    client: AsyncClient,
    admin_user: User,
    admin_headers: dict[str, str],
) -> None:
    resp = await client.get(USERS, headers=admin_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1


async def test_list_users_as_non_admin_forbidden(
    client: AsyncClient,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    resp = await client.get(USERS, headers=auth_headers)
    assert resp.status_code == 403, resp.text


async def test_admin_update_cannot_set_role(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
) -> None:
    """REGRESSION (privilege escalation): the generic admin PATCH must reject a
    ``role`` field — it accepts UserStatusUpdateRequest, which is strict."""
    target = await UserFactory.create(db_session, role=UserRole.CUSTOMER)
    resp = await client.patch(
        f"{USERS}/{target.id}",
        json={"role": "admin"},
        headers=admin_headers,
    )
    assert resp.status_code == 422, resp.text


async def test_role_change_forbidden_for_admin(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
) -> None:
    """REGRESSION: an ADMIN (not SUPERADMIN) cannot use the dedicated role
    endpoint."""
    target = await UserFactory.create(db_session, role=UserRole.CUSTOMER)
    resp = await client.patch(
        f"{USERS}/{target.id}/role",
        json={"role": "admin"},
        headers=admin_headers,
    )
    assert resp.status_code == 403, resp.text


async def test_role_change_allowed_for_superadmin(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Only a SUPERADMIN can change roles via the ``/role`` endpoint."""
    from src.core.security import create_access_token

    superadmin = await UserFactory.create(db_session, role=UserRole.SUPERADMIN)
    token, _ = create_access_token(
        str(superadmin.id), extra_claims={"role": superadmin.role.value}
    )
    headers = {"Authorization": f"Bearer {token}"}

    target = await UserFactory.create(db_session, role=UserRole.CUSTOMER)
    resp = await client.patch(
        f"{USERS}/{target.id}/role",
        json={"role": "admin"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["role"] == UserRole.ADMIN.value


async def test_toggle_user_status_deactivates(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_user: User,
    admin_headers: dict[str, str],
) -> None:
    target = await UserFactory.create(db_session, role=UserRole.CUSTOMER)
    resp = await client.patch(
        f"{USERS}/{target.id}/status",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_active"] is False
