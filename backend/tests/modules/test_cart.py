"""Cart module tests."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import ConflictError, NotFoundError
from src.modules.cart.service import CartService

from tests.factories import ProductFactory


@pytest.mark.asyncio
async def test_get_empty_cart(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test getting an empty cart returns default response."""
    user_id = uuid.uuid4()
    service = CartService(db_session, redis_client)

    cart = await service.get_cart(user_id)

    assert cart.items == []
    assert cart.total_items == 0
    assert cart.subtotal == Decimal("0")
    assert cart.currency == "UZS"


@pytest.mark.asyncio
async def test_add_item_to_cart(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test adding an item to cart."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("100.50"),
        stock=10,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)
    cart = await service.add_item(user_id, product.id, quantity=2)

    assert len(cart.items) == 1
    assert cart.items[0].product_id == product.id
    assert cart.items[0].quantity == 2
    assert cart.items[0].unit_price == Decimal("100.50")
    assert cart.items[0].line_total == Decimal("201.00")
    assert cart.total_items == 2
    assert cart.subtotal == Decimal("201.00")
    assert cart.currency == "UZS"


@pytest.mark.asyncio
async def test_add_item_exceeds_stock(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test adding item quantity that exceeds stock raises error."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("50.00"),
        stock=5,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    with pytest.raises(ConflictError) as exc:
        await service.add_item(user_id, product.id, quantity=10)

    assert "exceeds available stock" in str(exc.value).lower()
    assert exc.value.details["available"] == 5


@pytest.mark.asyncio
async def test_add_item_nonexistent_product(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test adding item for nonexistent product raises error."""
    user_id = uuid.uuid4()
    fake_id = uuid.uuid4()

    service = CartService(db_session, redis_client)

    with pytest.raises(NotFoundError) as exc:
        await service.add_item(user_id, fake_id, quantity=1)

    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_add_item_inactive_product(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test adding item for inactive product raises error."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("50.00"),
        stock=10,
        is_active=False,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    with pytest.raises(NotFoundError) as exc:
        await service.add_item(user_id, product.id, quantity=1)

    assert "not found" in str(exc.value).lower() or "unavailable" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_set_item_quantity(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test setting item quantity."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("25.00"),
        stock=20,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    # Add initial quantity
    await service.add_item(user_id, product.id, quantity=5)

    # Set new quantity
    cart = await service.set_item(user_id, product.id, quantity=10)

    assert len(cart.items) == 1
    assert cart.items[0].quantity == 10
    assert cart.items[0].line_total == Decimal("250.00")


@pytest.mark.asyncio
async def test_set_item_zero_removes_item(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test setting quantity to zero removes item from cart."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("30.00"),
        stock=10,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    # Add item
    await service.add_item(user_id, product.id, quantity=3)

    # Set quantity to zero
    cart = await service.set_item(user_id, product.id, quantity=0)

    assert len(cart.items) == 0
    assert cart.total_items == 0


@pytest.mark.asyncio
async def test_remove_item(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test removing an item from cart."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("40.00"),
        stock=10,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    # Add item
    await service.add_item(user_id, product.id, quantity=2)

    # Remove item
    cart = await service.remove_item(user_id, product.id)

    assert len(cart.items) == 0
    assert cart.total_items == 0


@pytest.mark.asyncio
async def test_clear_cart(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test clearing entire cart."""
    user_id = uuid.uuid4()
    product1 = await ProductFactory.create(
        db_session,
        name="Product 1",
        price=Decimal("10.00"),
        stock=10,
        currency="UZS",
    )
    product2 = await ProductFactory.create(
        db_session,
        name="Product 2",
        price=Decimal("20.00"),
        stock=10,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    # Add multiple items
    await service.add_item(user_id, product1.id, quantity=2)
    await service.add_item(user_id, product2.id, quantity=3)

    # Clear cart
    await service.clear(user_id)

    cart = await service.get_cart(user_id)
    assert len(cart.items) == 0
    assert cart.total_items == 0


@pytest.mark.asyncio
async def test_currency_consistency_validation(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test that adding products with different currencies raises error."""
    user_id = uuid.uuid4()
    product1 = await ProductFactory.create(
        db_session,
        name="Product 1",
        price=Decimal("100.00"),
        stock=10,
        currency="UZS",
    )
    product2 = await ProductFactory.create(
        db_session,
        name="Product 2",
        price=Decimal("50.00"),
        stock=10,
        currency="USD",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    # Add first product
    await service.add_item(user_id, product1.id, quantity=1)

    # Try to add product with different currency
    with pytest.raises(ConflictError) as exc:
        await service.add_item(user_id, product2.id, quantity=1)

    assert "different currency" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_stale_entry_cleanup(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test that stale entries (inactive/deleted products) are cleaned up."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("100.00"),
        stock=10,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    # Add item to cart
    await service.add_item(user_id, product.id, quantity=2)

    # Deactivate product
    product.is_active = False
    await db_session.commit()

    # Get cart - stale entry should be removed
    cart = await service.get_cart(user_id)

    assert len(cart.items) == 0
    assert cart.total_items == 0


@pytest.mark.asyncio
async def test_get_raw_cart(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test getting raw cart data for checkout."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("100.00"),
        stock=10,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    # Add items
    await service.add_item(user_id, product.id, quantity=3)

    # Get raw cart
    raw = await service.get_raw(user_id)

    assert product.id in raw
    assert raw[product.id] == 3
    assert isinstance(raw, dict)


@pytest.mark.asyncio
async def test_add_same_product_increments_quantity(
    db_session: AsyncSession, redis_client: object
) -> None:
    """Test that adding same product increments quantity."""
    user_id = uuid.uuid4()
    product = await ProductFactory.create(
        db_session,
        name="Test Product",
        price=Decimal("50.00"),
        stock=10,
        currency="UZS",
    )
    await db_session.commit()

    service = CartService(db_session, redis_client)

    # Add first time
    cart = await service.add_item(user_id, product.id, quantity=2)
    assert cart.items[0].quantity == 2

    # Add same product again
    cart = await service.add_item(user_id, product.id, quantity=3)
    assert cart.items[0].quantity == 5
    assert cart.total_items == 5
