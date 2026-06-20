"""Catalog business logic."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.core.pagination import Page, PaginationParams
from src.core.utils import generate_slug
from src.modules.catalog.filters import ProductFilters
from src.modules.catalog.models import Category, Product
from src.modules.catalog.repository import (
    CategoryRepository,
    ProductImageRepository,
    ProductRepository,
)
from src.modules.catalog.schemas import (
    CategoryCreateRequest,
    CategoryUpdateRequest,
    ProductCreateRequest,
    ProductUpdateRequest,
)


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CategoryRepository(session)

    async def create(self, data: CategoryCreateRequest) -> Category:
        if data.parent_id and not await self.repo.get(data.parent_id):
            raise ValidationError("Parent category does not exist.")
        payload = data.model_dump()
        payload["slug"] = generate_slug(data.name, await self.repo.get_all_slugs())
        return await self.repo.create(payload)

    async def get(self, category_id: uuid.UUID) -> Category:
        category = await self.repo.get(category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        return category

    async def list_all(self) -> list[Category]:
        return await self.repo.list_all()

    async def update(
        self, category_id: uuid.UUID, data: CategoryUpdateRequest
    ) -> Category:
        category = await self.get(category_id)
        if data.parent_id == category_id:
            raise ValidationError("A category cannot be its own parent.")
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload:
            payload["slug"] = generate_slug(
                payload["name"], await self.repo.get_all_slugs(exclude_id=category_id)
            )
        return await self.repo.update(category, payload)

    async def delete(self, category_id: uuid.UUID) -> None:
        category = await self.get(category_id)
        await self.repo.delete(category)


class ProductService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductRepository(session)
        self.images = ProductImageRepository(session)
        self.categories = CategoryRepository(session)

    async def create(self, data: ProductCreateRequest) -> Product:
        if not await self.categories.get(data.category_id):
            raise ValidationError("Category does not exist.")
        payload = data.model_dump(exclude={"attributes"})
        payload["slug"] = generate_slug(data.name, await self.repo.get_all_slugs())
        product = await self.repo.create(payload)
        if data.attributes:
            await self.repo.replace_attributes(
                product, [a.model_dump() for a in data.attributes]
            )
        loaded = await self.repo.get_with_relations(product.id)
        assert loaded is not None  # just created
        return loaded

    async def get(self, product_id: uuid.UUID) -> Product:
        product = await self.repo.get_with_relations(product_id)
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    async def get_by_slug(self, slug: str) -> Product:
        product = await self.repo.get_by_slug(slug)
        if product is None:
            raise NotFoundError("Product not found.")
        return product

    async def search(
        self,
        filters: ProductFilters,
        params: PaginationParams,
        sort: str = "-created_at",
    ) -> Page[Product]:
        items, total = await self.repo.search(
            filters, offset=params.offset, limit=params.limit, sort=sort
        )
        return Page.create(items, total, params)

    async def update(
        self, product_id: uuid.UUID, data: ProductUpdateRequest
    ) -> Product:
        product = await self.get(product_id)
        if data.category_id and not await self.categories.get(data.category_id):
            raise ValidationError("Category does not exist.")
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload:
            payload["slug"] = generate_slug(
                payload["name"], await self.repo.get_all_slugs(exclude_id=product_id)
            )
        await self.repo.update(product, payload)
        return await self.get(product_id)

    async def delete(self, product_id: uuid.UUID) -> None:
        product = await self.repo.get(product_id)
        if product is None:
            raise NotFoundError("Product not found.")
        await self.repo.delete(product)
