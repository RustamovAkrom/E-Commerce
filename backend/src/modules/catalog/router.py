"""Catalog HTTP endpoints (public reads, admin writes)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.core.dependencies import DbSession, require_admin
from src.core.pagination import Page, PaginationParams
from src.core.schemas import MessageResponse
from src.modules.catalog.filters import ProductFilters, product_filters
from src.modules.catalog.schemas import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
    ProductCreateRequest,
    ProductDetailResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from src.modules.catalog.service import CategoryService, ProductService

router = APIRouter()


# --- Categories -------------------------------------------------------------
@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: DbSession) -> list[CategoryResponse]:
    categories = await CategoryService(db).list_all()
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_category(
    data: CategoryCreateRequest, db: DbSession
) -> CategoryResponse:
    category = await CategoryService(db).create(data)
    return CategoryResponse.model_validate(category)


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(require_admin)],
)
async def update_category(
    category_id: uuid.UUID, data: CategoryUpdateRequest, db: DbSession
) -> CategoryResponse:
    category = await CategoryService(db).update(category_id, data)
    return CategoryResponse.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
async def delete_category(
    category_id: uuid.UUID, db: DbSession
) -> MessageResponse:
    await CategoryService(db).delete(category_id)
    return MessageResponse(message="Category deleted.")


# --- Products ---------------------------------------------------------------
@router.get("/products", response_model=Page[ProductResponse])
async def list_products(
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
    filters: Annotated[ProductFilters, Depends(product_filters)],
    sort: Annotated[str, Query(pattern=r"^-?(created_at|price|name)$")] = "-created_at",
) -> Page[ProductResponse]:
    page = await ProductService(db).search(filters, params, sort)
    return page.map(ProductResponse.model_validate)


@router.get("/products/slug/{slug}", response_model=ProductDetailResponse)
async def get_product_by_slug(slug: str, db: DbSession) -> ProductDetailResponse:
    product = await ProductService(db).get_by_slug(slug)
    return ProductDetailResponse.model_validate(product)


@router.get("/products/{product_id}", response_model=ProductDetailResponse)
async def get_product(product_id: uuid.UUID, db: DbSession) -> ProductDetailResponse:
    product = await ProductService(db).get(product_id)
    return ProductDetailResponse.model_validate(product)


@router.post(
    "/products",
    response_model=ProductDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_product(
    data: ProductCreateRequest, db: DbSession
) -> ProductDetailResponse:
    product = await ProductService(db).create(data)
    return ProductDetailResponse.model_validate(product)


@router.patch(
    "/products/{product_id}",
    response_model=ProductDetailResponse,
    dependencies=[Depends(require_admin)],
)
async def update_product(
    product_id: uuid.UUID, data: ProductUpdateRequest, db: DbSession
) -> ProductDetailResponse:
    product = await ProductService(db).update(product_id, data)
    return ProductDetailResponse.model_validate(product)


@router.delete(
    "/products/{product_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
async def delete_product(
    product_id: uuid.UUID, db: DbSession
) -> MessageResponse:
    await ProductService(db).delete(product_id)
    return MessageResponse(message="Product deleted.")
