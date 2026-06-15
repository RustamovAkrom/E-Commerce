"""Review business logic.

Customers may post one review per product, edit or delete their own, and read
the approved reviews of any product. Admins moderate (approve/hide) and may
remove any review. Posting is gated on the product actually existing.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    PermissionDeniedError,
)
from src.core.pagination import Page, PaginationParams
from src.modules.catalog.repository import ProductRepository
from src.modules.reviews.models import Review
from src.modules.reviews.repository import ReviewRepository
from src.modules.reviews.schemas import (
    ProductRatingSummary,
    ReviewCreateRequest,
    ReviewUpdateRequest,
)


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ReviewRepository(session)
        self.products = ProductRepository(session)

    async def create(
        self,
        product_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ReviewCreateRequest,
    ) -> Review:
        product = await self.products.get(product_id)
        if product is None:
            raise NotFoundError("Product not found.")
        if await self.repo.get_user_review(product_id, user_id) is not None:
            raise AlreadyExistsError("You have already reviewed this product.")
        return await self.repo.create(
            {
                "product_id": product_id,
                "user_id": user_id,
                "rating": data.rating,
                "title": data.title,
                "comment": data.comment,
            }
        )

    async def list_for_product(
        self, product_id: uuid.UUID, params: PaginationParams
    ) -> Page[Review]:
        items, total = await self.repo.list_for_product(
            product_id,
            offset=params.offset,
            limit=params.limit,
            approved_only=True,
        )
        return Page.create(items, total, params)

    async def rating_summary(
        self, product_id: uuid.UUID
    ) -> ProductRatingSummary:
        average, count = await self.repo.rating_summary(product_id)
        return ProductRatingSummary(
            product_id=product_id,
            average_rating=round(average, 2),
            review_count=count,
        )

    async def _get_owned(
        self, review_id: uuid.UUID, user_id: uuid.UUID
    ) -> Review:
        review = await self.repo.get(review_id)
        if review is None:
            raise NotFoundError("Review not found.")
        if review.user_id != user_id:
            raise PermissionDeniedError("This review does not belong to you.")
        return review

    async def update(
        self,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ReviewUpdateRequest,
    ) -> Review:
        review = await self._get_owned(review_id, user_id)
        return await self.repo.update(review, data.model_dump(exclude_unset=True))

    async def delete(self, review_id: uuid.UUID, user_id: uuid.UUID) -> None:
        review = await self._get_owned(review_id, user_id)
        await self.repo.delete(review)

    # --- Admin --------------------------------------------------------------
    async def list_all(self, params: PaginationParams) -> Page[Review]:
        items, total = await self.repo.list_all(
            offset=params.offset, limit=params.limit
        )
        return Page.create(items, total, params)

    async def moderate(
        self, review_id: uuid.UUID, *, is_approved: bool
    ) -> Review:
        review = await self.repo.get(review_id)
        if review is None:
            raise NotFoundError("Review not found.")
        return await self.repo.update(review, {"is_approved": is_approved})

    async def admin_delete(self, review_id: uuid.UUID) -> None:
        review = await self.repo.get(review_id)
        if review is None:
            raise NotFoundError("Review not found.")
        await self.repo.delete(review)
