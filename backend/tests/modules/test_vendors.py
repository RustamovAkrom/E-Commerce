"""Vendor endpoint tests: apply, read own storefront, admin approval (with
role promotion), public listing/slug lookup, and admin-only moderation guard.

The vendors router is mounted unconditionally (the platform is always a
multi-vendor marketplace), so these run without a marketplace-mode skip.
"""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.enums import UserRole
from src.core.security import create_access_token
from src.modules.users.models import User

VENDORS = "/api/v1/vendors"

_APPLY = {
    "name": "Acme Storefront",
    "description": "We sell everything.",
    "contact_email": "shop@acme.com",
    "contact_phone": "+998901112233",
}


def _bearer(user: User) -> dict[str, str]:
    token, _ = create_access_token(
        str(user.id), extra_claims={"role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


async def test_apply_and_get_my_vendor(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    resp = await client.post(
        f"{VENDORS}/apply", json=_APPLY, headers=auth_headers
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "Acme Storefront"
    assert body["user_id"] == str(customer_user.id)
    assert body["status"] == "pending"
    assert body["slug"]

    mine = await client.get(f"{VENDORS}/me", headers=auth_headers)
    assert mine.status_code == 200, mine.text
    assert mine.json()["id"] == body["id"]


async def test_admin_approve_promotes_owner_to_vendor(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    applied = await client.post(
        f"{VENDORS}/apply", json=_APPLY, headers=auth_headers
    )
    assert applied.status_code == 201, applied.text
    vendor_id = applied.json()["id"]

    approved = await client.patch(
        f"{VENDORS}/{vendor_id}",
        json={"status": "approved"},
        headers=admin_headers,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    # Approving promotes the owning CUSTOMER to the VENDOR role.
    refreshed = (
        await db_session.execute(
            select(User).where(User.id == customer_user.id)
        )
    ).scalar_one()
    await db_session.refresh(refreshed)
    assert refreshed.role == UserRole.VENDOR


async def test_public_listing_and_slug_lookup(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    applied = await client.post(
        f"{VENDORS}/apply", json=_APPLY, headers=auth_headers
    )
    assert applied.status_code == 201, applied.text
    vendor_id = applied.json()["id"]
    slug = applied.json()["slug"]

    # Pending vendors are not public yet.
    before = await client.get(VENDORS)
    assert before.status_code == 200, before.text
    assert before.json()["total"] == 0

    approve = await client.patch(
        f"{VENDORS}/{vendor_id}",
        json={"status": "approved"},
        headers=admin_headers,
    )
    assert approve.status_code == 200, approve.text

    # Approved vendors appear in the public listing.
    listed = await client.get(VENDORS)
    assert listed.status_code == 200, listed.text
    page = listed.json()
    assert page["total"] == 1
    assert page["items"][0]["slug"] == slug

    by_slug = await client.get(f"{VENDORS}/slug/{slug}")
    assert by_slug.status_code == 200, by_slug.text
    assert by_slug.json()["id"] == vendor_id


async def test_non_admin_cannot_approve(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    applied = await client.post(
        f"{VENDORS}/apply", json=_APPLY, headers=auth_headers
    )
    assert applied.status_code == 201, applied.text
    vendor_id = applied.json()["id"]

    # A customer hitting the admin-gated update endpoint is forbidden.
    resp = await client.patch(
        f"{VENDORS}/{vendor_id}",
        json={"status": "approved"},
        headers=auth_headers,
    )
    assert resp.status_code == 403, resp.text
