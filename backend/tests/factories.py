"""Async object factories for tests.

Each ``create`` persists (commits) the object so it is visible to the separate
connection the HTTP client uses. Values are randomised with a short uuid suffix
to keep unique columns (email, slug) collision-free across a test run.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from src.core.enums import OrderStatus, UserRole
from src.core.security import hash_password
from src.modules.catalog.models import Category, Product
from src.modules.orders.models import Order, OrderItem
from src.modules.users.models import User

_DEFAULT_PASSWORD = "password123"


def _suffix() -> str:
    return uuid.uuid4().hex[:12]


class UserFactory:
    """Create :class:`User` rows with a hashed password."""

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        email: str | None = None,
        password: str = _DEFAULT_PASSWORD,
        role: UserRole = UserRole.CUSTOMER,
        full_name: str = "Test User",
        is_active: bool = True,
        is_verified: bool = True,
    ) -> User:
        user = User(
            email=(email or f"user-{_suffix()}@example.com").lower(),
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=is_active,
            is_verified=is_verified,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


class CategoryFactory:
    """Create :class:`Category` rows."""

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        name: str = "Test Category",
        slug: str | None = None,
        is_active: bool = True,
    ) -> Category:
        category = Category(
            name=name,
            slug=slug or f"cat-{_suffix()}",
            is_active=is_active,
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


class ProductFactory:
    """Create :class:`Product` rows (with an owning category if none given)."""

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        category: Category | None = None,
        name: str | None = None,
        slug: str | None = None,
        price: Decimal = Decimal("100.00"),
        currency: str = "UZS",
        stock: int = 10,
        is_active: bool = True,
    ) -> Product:
        if category is None:
            category = await CategoryFactory.create(session)
        product = Product(
            category_id=category.id,
            name=name or f"Product {_suffix()}",
            slug=slug or f"product-{_suffix()}",
            price=price,
            currency=currency,
            stock=stock,
            is_active=is_active,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product


class OrderFactory:
    """Create :class:`Order` rows with line items.

    ``items`` is a list of ``{"product": Product, "quantity": int}`` dicts.
    """

    @staticmethod
    async def create(
        session: AsyncSession,
        *,
        user: User,
        items: list[dict[str, Any]] | None = None,
        status: OrderStatus = OrderStatus.PENDING,
        shipping_address: dict[str, Any] | None = None,
    ) -> Order:
        order = Order(
            user_id=user.id,
            status=status,
            total_amount=Decimal("0"),
            currency="UZS",
            shipping_address=shipping_address
            or {
                "full_name": "Test User",
                "phone": "+998901234567",
                "address": "1 Test Street",
                "city": "Tashkent",
                "country": "UZ",
            },
        )
        session.add(order)
        await session.flush()  # assigns order.id

        total = Decimal("0")
        for item in items or []:
            product: Product = item["product"]
            quantity = int(item.get("quantity", 1))
            session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )
            total += product.price * quantity

        order.total_amount = total
        await session.commit()
        await session.refresh(order)
        return order
