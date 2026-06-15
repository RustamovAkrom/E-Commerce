"""Review HTTP endpoints.

Public: read approved reviews and the rating summary for a product. Customer:
create / edit / delete own review. Admin: list all, moderate, hard-delete.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import CurrentUser, DbSession, require_admin
from src.core.pagination import Page, PaginationParams
from src.core.schemas import MessageResponse
from src.modules.reviews.schemas import (
    ProductRatingSummary,
    ReviewCreateRequest,
    ReviewModerateRequest,
    ReviewResponse,
    ReviewUpdateRequest,
)
from src.modules.reviews.service import ReviewService

router = APIRouter()


# --- Public -----------------------------------------------------------------
@router.get(
    "/products/{product_id}/reviews",
    response_model=Page[ReviewResponse],
)
async def list_product_reviews(
    product_id: uuid.UUID,
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
) -> Page[ReviewResponse]:
    page = await ReviewService(db).list_for_product(product_id, params)
    return page.map(ReviewResponse.model_validate)


@router.get(
    "/products/{product_id}/reviews/summary",
    response_model=ProductRatingSummary,
)
async def product_rating_summary(
    product_id: uuid.UUID,
    db: DbSession,
) -> ProductRatingSummary:
    return await ReviewService(db).rating_summary(product_id)


# --- Customer ---------------------------------------------------------------
@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    product_id: uuid.UUID,
    data: ReviewCreateRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> ReviewResponse:
    review = await ReviewService(db).create(product_id, user.id, data)  # type: ignore[attr-defined]
    return ReviewResponse.model_validate(review)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: uuid.UUID,
    data: ReviewUpdateRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> ReviewResponse:
    review = await ReviewService(db).update(review_id, user.id, data)  # type: ignore[attr-defined]
    return ReviewResponse.model_validate(review)


@router.delete("/reviews/{review_id}", response_model=MessageResponse)
async def delete_review(
    review_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> MessageResponse:
    await ReviewService(db).delete(review_id, user.id)  # type: ignore[attr-defined]
    return MessageResponse(message="Review deleted.")


# --- Admin ------------------------------------------------------------------
@router.get(
    "/reviews",
    response_model=Page[ReviewResponse],
    dependencies=[Depends(require_admin)],
)
async def list_all_reviews(
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
) -> Page[ReviewResponse]:
    page = await ReviewService(db).list_all(params)
    return page.map(ReviewResponse.model_validate)


@router.patch(
    "/reviews/{review_id}/moderate",
    response_model=ReviewResponse,
    dependencies=[Depends(require_admin)],
)
async def moderate_review(
    review_id: uuid.UUID,
    data: ReviewModerateRequest,
    db: DbSession,
) -> ReviewResponse:
    review = await ReviewService(db).moderate(
        review_id, is_approved=data.is_approved
    )
    return ReviewResponse.model_validate(review)


@router.delete(
    "/reviews/{review_id}/admin",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
async def admin_delete_review(
    review_id: uuid.UUID,
    db: DbSession,
) -> MessageResponse:
    await ReviewService(db).admin_delete(review_id)
    return MessageResponse(message="Review deleted.")
