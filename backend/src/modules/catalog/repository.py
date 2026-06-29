"""Catalog repositories — DB queries only."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from src.core.base_repository import BaseRepository
from src.modules.catalog.filters import ProductFilters, resolve_sort
from src.modules.catalog.models import (
    Category,
    Product,
    ProductAttribute,
    ProductImage,
)


class CategoryRepository(BaseRepository[Category]):
    model = Category

    async def get_by_slug(self, slug: str) -> Category | None:
        return await self.get_by(slug=slug)

    async def list_all(self) -> list[Category]:
        stmt = (
            select(Category)
            .where(Category.is_deleted.is_(False))
            .order_by(Category.sort_order, Category.name)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ProductRepository(BaseRepository[Product]):
    model = Product

    async def get_with_relations(self, product_id: uuid.UUID) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.id == product_id, Product.is_deleted.is_(False))
            .options(
                selectinload(Product.images),
                selectinload(Product.attributes),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Product | None:
        stmt = (
            select(Product)
            .where(Product.slug == slug, Product.is_deleted.is_(False))
            .options(
                selectinload(Product.images),
                selectinload(Product.attributes),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many_by_ids(
        self, product_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Product]:
        """Batch-fetch non-deleted products by id, keyed by id.

        Lets callers (e.g. the cart) resolve many products in a single query
        instead of issuing one ``get`` per id (N+1).
        """
        if not product_ids:
            return {}
        stmt = select(Product).where(
            Product.id.in_(product_ids), Product.is_deleted.is_(False)
        )
        result = await self.session.execute(stmt)
        return {product.id: product for product in result.scalars().all()}

    async def search(
        self,
        filters: ProductFilters,
        *,
        offset: int,
        limit: int,
        sort: str = "-created_at",
    ) -> tuple[list[Product], int]:
        clauses = filters.to_clauses()
        base = select(Product).where(Product.is_deleted.is_(False))
        for clause in clauses:
            base = base.where(clause)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = int((await self.session.execute(count_stmt)).scalar_one())

        list_stmt = (
            base.options(selectinload(Product.images))
            .order_by(resolve_sort(sort))
            .offset(offset)
            .limit(limit)
        )
        items = list((await self.session.execute(list_stmt)).scalars().all())
        return items, total

    async def replace_attributes(
        self, product: Product, attributes: list[dict[str, str]]
    ) -> None:
        await self.session.refresh(product, ["attributes"])
        for existing in list(product.attributes):
            await self.session.delete(existing)
        for attr in attributes:
            self.session.add(ProductAttribute(product_id=product.id, **attr))
        await self.session.flush()


class ProductImageRepository(BaseRepository[ProductImage]):
    model = ProductImage

    async def get_for_product(
        self, image_id: uuid.UUID, product_id: uuid.UUID
    ) -> ProductImage | None:
        stmt = select(ProductImage).where(
            ProductImage.id == image_id,
            ProductImage.product_id == product_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_product(self, product_id: uuid.UUID) -> list[ProductImage]:
        stmt = (
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.sort_order, ProductImage.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def unset_primary_for_product(self, product_id: uuid.UUID) -> None:
        images = await self.list_for_product(product_id)
        for image in images:
            image.is_primary = False
            self.session.add(image)
        await self.session.flush()
