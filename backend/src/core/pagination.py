"""Generic, reusable pagination used by every module.

Repositories accept a ``PaginationParams`` and return a ``Page[T]``. The
router exposes ``PaginationParams`` as a FastAPI dependency so query params
``?page=&size=`` work everywhere consistently.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field

T = TypeVar("T")
R = TypeVar("R")


class PaginationParams:
    """FastAPI dependency capturing ``page`` and ``size`` query params."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="1-indexed page number"),
        size: int = Query(20, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.size = size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        return self.size


class Page(BaseModel, Generic[T]):
    """A page of results plus metadata."""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)
    pages: int = Field(ge=0)

    @classmethod
    def create(
        cls, items: list[T], total: int, params: PaginationParams
    ) -> "Page[T]":
        pages = (total + params.size - 1) // params.size if params.size else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )

    def map(self, fn: Callable[[T], R]) -> "Page[R]":
        """Return a new page with each item transformed by ``fn``.

        Used by routers to convert a page of ORM objects into a page of
        Pydantic response schemas without losing pagination metadata.
        """
        return Page[R](
            items=[fn(item) for item in self.items],
            total=self.total,
            page=self.page,
            size=self.size,
            pages=self.pages,
        )
