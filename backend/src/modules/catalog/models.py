"""Catalog ORM models: Category, Product, ProductImage, ProductAttribute."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    event,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from src.core.database import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from src.core.utils import generate_slug


class Category(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    parent: Mapped[Category | None] = relationship(
        "Category", remote_side="Category.id", backref="children"
    )

    @validates("name")
    def _generate_slug_from_name(self, key: str, name: str) -> str:  # noqa: ARG002
        self.slug = generate_slug(name)
        return name


class Product(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "products"

    # Nullable so admin/platform-level products can exist without a vendor.
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vendors.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="UZS", nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )

    category: Mapped[Category] = relationship("Category", backref="products")

    images: Mapped[list[ProductImage]] = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )
    attributes: Mapped[list[ProductAttribute]] = relationship(
        "ProductAttribute",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    @validates("name")
    def _generate_slug_from_name(self, key: str, name: str) -> str:  # noqa: ARG002
        self.slug = generate_slug(name)
        return name


class ProductImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_images"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="images")


class ProductAttribute(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "product_attributes"
    __table_args__ = (
        UniqueConstraint("product_id", "key", name="uq_product_attribute_key"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[str] = mapped_column(String(512), nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="attributes")


def _set_unique_slug(connection: Any, model: type[Any], target: Any) -> None:
    stmt = select(model.slug).where(model.is_deleted.is_(False))
    if target.id is not None:
        stmt = stmt.where(model.id != target.id)
    existing_slugs = set(connection.execute(stmt).scalars().all())
    target.slug = generate_slug(target.name, existing_slugs)


@event.listens_for(Category, "before_insert")
@event.listens_for(Category, "before_update")
def _set_unique_category_slug(mapper: Any, connection: Any, target: Category) -> None:  # noqa: ARG001
    _set_unique_slug(connection, Category, target)


@event.listens_for(Product, "before_insert")
@event.listens_for(Product, "before_update")
def _set_unique_product_slug(mapper: Any, connection: Any, target: Product) -> None:  # noqa: ARG001
    _set_unique_slug(connection, Product, target)
