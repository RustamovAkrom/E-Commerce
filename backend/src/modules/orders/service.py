"""Order business logic.

Order creation is the critical path: it reads the user's cart, atomically
reserves stock for every line via the inventory service, persists the order
and its items, then clears the cart. If any reservation fails the whole thing
rolls back (the surrounding ``get_db`` dependency owns the transaction).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import OrderStatus, UserRole
from src.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from src.core.pagination import Page, PaginationParams
from src.modules.cart.service import CartService
from src.modules.catalog.repository import ProductRepository
from src.modules.inventory.service import InventoryService
from src.modules.orders.models import Order, OrderItem
from src.modules.orders.repository import OrderRepository
from src.modules.orders.schemas import OrderCreateRequest
from src.modules.orders.state_machine import (
    CUSTOMER_CANCELLABLE,
    STOCK_RELEASING,
    ensure_transition,
)


class OrderService:
    def __init__(self, session: AsyncSession, redis_client: redis.Redis) -> None:
        self.session = session
        self.repo = OrderRepository(session)
        self.products = ProductRepository(session)
        self.inventory = InventoryService(session)
        self.cart = CartService(session, redis_client)

    async def create_from_cart(
        self, user_id: uuid.UUID, data: OrderCreateRequest
    ) -> Order:
        cart_items = await self.cart.get_raw(user_id)
        if not cart_items:
            raise ValidationError("Cannot create an order from an empty cart.")

        order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING,
            total_amount=Decimal("0"),
            shipping_address=data.shipping_address.model_dump(),
            note=data.note,
        )
        self.session.add(order)
        await self.session.flush()  # assigns order.id

        total = Decimal("0")
        currency: str | None = None
        for product_id, quantity in cart_items.items():
            product = await self.products.get(product_id)
            if product is None or not product.is_active:
                raise ConflictError(
                    "A product in your cart is no longer available.",
                    details={"product_id": str(product_id)},
                )
            # An order must be settled in a single currency; the cart guards
            # this too, but the order is the source of truth for money.
            if currency is None:
                currency = product.currency
            elif product.currency != currency:
                raise ValidationError(
                    "Cart contains products with different currencies.",
                    details={
                        "expected_currency": currency,
                        "product_currency": product.currency,
                    },
                )
            # Atomic, race-safe reservation; raises ConflictError if short.
            await self.inventory.reserve(
                product_id, quantity, reference=f"order:{order.id}"
            )
            line_total = product.price * quantity
            total += line_total
            self.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=quantity,
                    unit_price=product.price,
                )
            )

        order.total_amount = total
        order.currency = currency or "UZS"
        await self.session.flush()

        # Cart is consumed once the order is staged.
        await self.cart.clear(user_id)

        created = await self.repo.get_with_items(order.id)
        assert created is not None
        return created

    async def get(self, order_id: uuid.UUID) -> Order:
        order = await self.repo.get_with_items(order_id)
        if order is None:
            raise NotFoundError("Order not found.")
        return order

    async def get_for_user(
        self, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> Order:
        order = await self.get(order_id)
        if order.user_id != user_id:
            raise PermissionDeniedError("This order does not belong to you.")
        return order

    async def list_for_user(
        self, user_id: uuid.UUID, params: PaginationParams
    ) -> Page[Order]:
        items, total = await self.repo.list_for_user(
            user_id, offset=params.offset, limit=params.limit
        )
        return Page.create(items, total, params)

    async def list_all(self, params: PaginationParams) -> Page[Order]:
        items, total = await self.repo.list_all(
            offset=params.offset, limit=params.limit
        )
        return Page.create(items, total, params)

    async def transition(
        self, order_id: uuid.UUID, target: OrderStatus
    ) -> Order:
        """Admin-driven status change, validated by the state machine."""
        order = await self.get(order_id)
        ensure_transition(order.status, target)
        if target in STOCK_RELEASING:
            await self._release_stock(order)
        order.status = target
        self.session.add(order)
        await self.session.flush()
        return order

    async def cancel(
        self, order_id: uuid.UUID, *, user_id: uuid.UUID, role: UserRole
    ) -> Order:
        order = await self.get(order_id)
        is_owner = order.user_id == user_id
        is_staff = role in (UserRole.ADMIN, UserRole.SUPERADMIN)
        if not is_owner and not is_staff:
            raise PermissionDeniedError("Cannot cancel this order.")
        if is_owner and not is_staff and order.status not in CUSTOMER_CANCELLABLE:
            raise ConflictError(
                "Order can no longer be cancelled.",
                details={"status": order.status.value},
            )
        return await self.transition(order_id, OrderStatus.CANCELLED)

    async def mark_paid(self, order_id: uuid.UUID) -> Order:
        """Called by the payments module once a payment succeeds."""
        order = await self.get(order_id)
        if order.status == OrderStatus.PAID:
            return order
        ensure_transition(order.status, OrderStatus.PAID)
        order.status = OrderStatus.PAID
        self.session.add(order)
        await self.session.flush()
        return order

    async def mark_refunded(self, order_id: uuid.UUID) -> Order:
        """Called by the payments module when a payment is refunded.

        Releases the reserved stock back to inventory. Idempotent: a repeat
        call once the order is already refunded is a no-op.
        """
        order = await self.get(order_id)
        if order.status == OrderStatus.REFUNDED:
            return order
        return await self.transition(order_id, OrderStatus.REFUNDED)

    async def _release_stock(self, order: Order) -> None:
        for item in order.items:
            await self.inventory.release(
                item.product_id, item.quantity, reference=f"order:{order.id}"
            )
