"""Review endpoint tests: create/list, duplicates, validation, summary,
ownership, and admin moderation/deletion."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.enums import UserRole
from src.core.security import create_access_token
from src.modules.users.models import User

from tests.factories import ProductFactory, UserFactory

API = "/api/v1"


def _bearer(user: User) -> dict[str, str]:
    token, _ = create_access_token(
        str(user.id), extra_claims={"role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}


async def test_create_and_list_review(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(db_session)

    resp = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 5, "title": "Great", "comment": "Loved it"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["rating"] == 5
    assert body["title"] == "Great"
    assert body["product_id"] == str(product.id)
    assert body["user_id"] == str(customer_user.id)

    # Read it back in the public list (approved by default).
    listed = await client.get(f"{API}/products/{product.id}/reviews")
    assert listed.status_code == 200, listed.text
    page = listed.json()
    assert page["total"] == 1
    assert page["items"][0]["id"] == body["id"]


async def test_duplicate_review_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(db_session)

    first = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 4},
        headers=auth_headers,
    )
    assert first.status_code == 201, first.text

    # A second review by the same user on the same product is a conflict.
    second = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 3},
        headers=auth_headers,
    )
    assert second.status_code == 409, second.text


async def test_rating_out_of_bounds_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(db_session)

    too_low = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 0},
        headers=auth_headers,
    )
    assert too_low.status_code == 422, too_low.text

    too_high = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 6},
        headers=auth_headers,
    )
    assert too_high.status_code == 422, too_high.text


async def test_rating_summary(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    product = await ProductFactory.create(db_session)
    user_a = await UserFactory.create(db_session, role=UserRole.CUSTOMER)
    user_b = await UserFactory.create(db_session, role=UserRole.CUSTOMER)

    # Reviews are approved by default; both count toward the summary.
    resp_a = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 4},
        headers=_bearer(user_a),
    )
    assert resp_a.status_code == 201, resp_a.text
    resp_b = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 2},
        headers=_bearer(user_b),
    )
    assert resp_b.status_code == 201, resp_b.text

    summary = await client.get(f"{API}/products/{product.id}/reviews/summary")
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["review_count"] == 2
    assert body["average_rating"] == 3.0


async def test_ownership_enforced_on_update_and_delete(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(db_session)

    # User A (the customer fixture) owns the review.
    created = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 5},
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text
    review_id = created.json()["id"]

    # User B cannot edit or delete it — the service raises PermissionDenied (403).
    user_b = await UserFactory.create(db_session, role=UserRole.CUSTOMER)
    headers_b = _bearer(user_b)

    patched = await client.patch(
        f"{API}/reviews/{review_id}",
        json={"rating": 1},
        headers=headers_b,
    )
    assert patched.status_code == 403, patched.text

    deleted = await client.delete(
        f"{API}/reviews/{review_id}", headers=headers_b
    )
    assert deleted.status_code == 403, deleted.text


async def test_admin_moderate_and_delete(
    client: AsyncClient,
    db_session: AsyncSession,
    customer_user: User,
    auth_headers: dict[str, str],
    admin_headers: dict[str, str],
) -> None:
    product = await ProductFactory.create(db_session)

    created = await client.post(
        f"{API}/products/{product.id}/reviews",
        json={"rating": 5},
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text
    review_id = created.json()["id"]

    # Admin hides the review (moderation flag flips to False).
    moderated = await client.patch(
        f"{API}/reviews/{review_id}/moderate",
        json={"is_approved": False},
        headers=admin_headers,
    )
    assert moderated.status_code == 200, moderated.text
    assert moderated.json()["is_approved"] is False

    # A hidden review no longer appears in the public list.
    listed = await client.get(f"{API}/products/{product.id}/reviews")
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 0

    # Admin hard-deletes the review.
    deleted = await client.delete(
        f"{API}/reviews/{review_id}/admin", headers=admin_headers
    )
    assert deleted.status_code == 200, deleted.text

    # The row is soft-deleted and no longer retrievable by the admin list.
    all_reviews = await client.get(f"{API}/reviews", headers=admin_headers)
    assert all_reviews.status_code == 200, all_reviews.text
    assert all_reviews.json()["total"] == 0
