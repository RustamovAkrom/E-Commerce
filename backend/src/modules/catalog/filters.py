"""Query filter builder for the product catalog.

Translates request query parameters into SQLAlchemy ``WHERE`` clauses without
leaking ORM details into the router. Used by :class:`ProductRepository`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Any

from fastapi import Query
from sqlalchemy import ColumnElement, or_

from src.modules.catalog.models import Product


@dataclass(slots=True)
class ProductFilters:
    """Captured product filter/search parameters."""

    search: str | None = None
    category_id: uuid.UUID | None = None
    vendor_id: uuid.UUID | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    in_stock: bool | None = None
    is_active: bool | None = True

    def to_clauses(self) -> list[ColumnElement[bool]]:
        clauses: list[ColumnElement[bool]] = []
        if self.search:
            pattern = f"%{self.search.strip()}%"
            clauses.append(
                or_(
                    Product.name.ilike(pattern),
                    Product.description.ilike(pattern),
                    Product.sku.ilike(pattern),
                )
            )
        if self.category_id is not None:
            clauses.append(Product.category_id == self.category_id)
        if self.vendor_id is not None:
            clauses.append(Product.vendor_id == self.vendor_id)
        if self.min_price is not None:
            clauses.append(Product.price >= self.min_price)
        if self.max_price is not None:
            clauses.append(Product.price <= self.max_price)
        if self.in_stock is True:
            clauses.append(Product.stock > 0)
        if self.is_active is not None:
            clauses.append(Product.is_active.is_(self.is_active))
        return clauses


def product_filters(
    search: Annotated[str | None, Query(max_length=255)] = None,
    category_id: Annotated[uuid.UUID | None, Query()] = None,
    vendor_id: Annotated[uuid.UUID | None, Query()] = None,
    min_price: Annotated[Decimal | None, Query(ge=0)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0)] = None,
    in_stock: Annotated[bool | None, Query()] = None,
) -> ProductFilters:
    """FastAPI dependency producing a :class:`ProductFilters`."""
    return ProductFilters(
        search=search,
        category_id=category_id,
        vendor_id=vendor_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
    )


_SORT_COLUMNS: dict[str, Any] = {
    "created_at": Product.created_at,
    "price": Product.price,
    "name": Product.name,
}


def resolve_sort(sort: str) -> Any:
    """Map a ``?sort=`` value like ``-price`` to an ORDER BY expression."""
    descending = sort.startswith("-")
    key = sort.lstrip("-")
    column = _SORT_COLUMNS.get(key, Product.created_at)
    return column.desc() if descending else column.asc()
