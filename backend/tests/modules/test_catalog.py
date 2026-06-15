"""Catalog endpoint tests: public reads and admin-only writes."""

from __future__ import annotations

from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import CategoryFactory, ProductFactory

CATALOG = "/api/v1/catalog"


async def test_list_products(client: AsyncClient, db_session: AsyncSession) -> None:
    category = await CategoryFactory.create(db_session)
    for _ in range(3):
        await ProductFactory.create(db_session, category=category)

    resp = await client.get(
        f"{CATALOG}/products", params={"page": 1, "size": 2}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["size"] == 2
    assert body["pages"] == 2
    assert len(body["items"]) == 2


async def test_get_product_by_slug(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    await ProductFactory.create(db_session, slug="cool-widget", name="Cool Widget")

    resp = await client.get(f"{CATALOG}/products/slug/cool-widget")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["slug"] == "cool-widget"
    assert body["name"] == "Cool Widget"
    # Detail response includes relationship collections.
    assert "images" in body
    assert "attributes" in body


async def test_create_product(
    client: AsyncClient, db_session: AsyncSession, admin_headers: dict[str, str]
) -> None:
    category = await CategoryFactory.create(db_session)
    payload = {
        "category_id": str(category.id),
        "name": "New Product",
        "slug": "new-product",
        "price": "199.99",
        "stock": 5,
    }
    resp = await client.post(
        f"{CATALOG}/products", json=payload, headers=admin_headers
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "New Product"
    assert body["slug"] == "new-product"
    assert Decimal(body["price"]) == Decimal("199.99")
    assert body["stock"] == 5


async def test_create_product_unauthorized(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict[str, str]
) -> None:
    category = await CategoryFactory.create(db_session)
    payload = {
        "category_id": str(category.id),
        "name": "Forbidden Product",
        "slug": "forbidden-product",
        "price": "10.00",
    }
    # A CUSTOMER token is authenticated but lacks the ADMIN role -> 403.
    resp = await client.post(
        f"{CATALOG}/products", json=payload, headers=auth_headers
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["error"] == "permission_denied"
