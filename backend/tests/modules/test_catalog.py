"""Catalog endpoint tests: public reads and admin-only writes."""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import CategoryFactory, ProductFactory

CATALOG = "/api/v1/catalog"


async def test_list_products(client: AsyncClient, db_session: AsyncSession) -> None:
    # Clear existing products first (need to clear related tables first due to FK constraints)
    from sqlalchemy import delete
    from src.modules.catalog.models import Product, ProductAttribute, ProductImage
    from src.modules.orders.models import OrderItem
    await db_session.execute(delete(OrderItem))
    await db_session.execute(delete(ProductImage))
    await db_session.execute(delete(ProductAttribute))
    await db_session.execute(delete(Product))
    await db_session.commit()

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
        "price": "199.99",
        "stock": 5,
    }
    resp = await client.post(
        f"{CATALOG}/products", json=payload, headers=admin_headers
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "New Product"
    assert body["slug"].startswith("new-product")
    assert Decimal(body["price"]) == Decimal("199.99")
    assert body["stock"] == 5


async def test_create_product_unauthorized(
    client: AsyncClient, db_session: AsyncSession, auth_headers: dict[str, str]
) -> None:
    category = await CategoryFactory.create(db_session)
    payload = {
        "category_id": str(category.id),
        "name": "Forbidden Product",
        "price": "10.00",
    }
    # A CUSTOMER token is authenticated but lacks the ADMIN role -> 403.
    resp = await client.post(
        f"{CATALOG}/products", json=payload, headers=auth_headers
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["error"] == "permission_denied"


async def test_upload_product_image(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    category = await CategoryFactory.create(db_session)
    product = await ProductFactory.create(db_session, category=category)

    def fake_upload_file(
        content: bytes, original_filename: str, content_type: str
    ) -> str:
        assert content == b"fake-image"
        assert original_filename == "product.png"
        assert content_type == "image/png"
        return "products/product.png"

    def fake_public_url(object_name: str) -> str:
        return f"http://localhost:9000/ecommerce/{object_name}"

    monkeypatch.setattr(
        "src.modules.catalog.service.upload_file",
        fake_upload_file,
    )
    monkeypatch.setattr(
        "src.modules.catalog.service.public_url",
        fake_public_url,
    )

    resp = await client.post(
        f"{CATALOG}/products/{product.id}/images",
        files={"file": ("product.png", b"fake-image", "image/png")},
        headers=admin_headers,
    )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["url"] == "http://localhost:9000/ecommerce/products/product.png"
    assert body["is_primary"] is True
    assert body["sort_order"] == 0

    detail = await client.get(f"{CATALOG}/products/{product.id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["images"][0]["id"] == body["id"]


async def test_set_primary_product_image(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_headers: dict[str, str],
) -> None:
    from src.modules.catalog.models import ProductImage

    category = await CategoryFactory.create(db_session)
    product = await ProductFactory.create(db_session, category=category)
    first = ProductImage(
        product_id=product.id,
        url="http://localhost:9000/ecommerce/first.png",
        is_primary=True,
        sort_order=0,
    )
    second = ProductImage(
        product_id=product.id,
        url="http://localhost:9000/ecommerce/second.png",
        is_primary=False,
        sort_order=1,
    )
    db_session.add_all([first, second])
    await db_session.commit()
    await db_session.refresh(second)

    resp = await client.patch(
        f"{CATALOG}/products/{product.id}/images/{second.id}/primary",
        headers=admin_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == str(second.id)
    assert resp.json()["is_primary"] is True


async def test_delete_product_image(
    client: AsyncClient,
    db_session: AsyncSession,
    admin_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.modules.catalog.models import ProductImage

    deleted: list[str] = []

    def fake_delete_file(object_name: str) -> None:
        deleted.append(object_name)

    monkeypatch.setattr(
        "src.modules.catalog.service.delete_file",
        fake_delete_file,
    )

    category = await CategoryFactory.create(db_session)
    product = await ProductFactory.create(db_session, category=category)
    image = ProductImage(
        product_id=product.id,
        url="http://localhost:9000/ecommerce/products/remove.png",
        is_primary=True,
        sort_order=0,
    )
    db_session.add(image)
    await db_session.commit()
    await db_session.refresh(image)

    resp = await client.delete(
        f"{CATALOG}/products/{product.id}/images/{image.id}",
        headers=admin_headers,
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["message"] == "Product image deleted."
    assert deleted == ["products/remove.png"]
