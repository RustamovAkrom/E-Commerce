"""Redis-backed shopping cart.

The cart is a Redis hash keyed ``cart:{user_id}`` mapping
``product_id -> quantity``. Product details and prices are resolved live from
the catalog when the cart is read, so price/stock are always current.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.exceptions import ConflictError, NotFoundError
from src.modules.cart.schemas import CartItemResponse, CartResponse
from src.modules.catalog.models import Product
from src.modules.catalog.repository import ProductRepository


class CartService:
    def __init__(self, session: AsyncSession, redis_client: redis.Redis) -> None:
        self.session = session
        self.redis = redis_client
        self.products = ProductRepository(session)

    @staticmethod
    def _key(user_id: uuid.UUID) -> str:
        return f"cart:{user_id}"

    async def _touch_ttl(self, user_id: uuid.UUID) -> None:
        await self.redis.expire(self._key(user_id), settings.CART_TTL_SECONDS)

    async def add_item(
        self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int
    ) -> CartResponse:
        product = await self.products.get(product_id)
        if product is None or not product.is_active:
            raise NotFoundError("Product not found or unavailable.")

        key = self._key(user_id)
        current = int(await self.redis.hget(key, str(product_id)) or 0)  # type: ignore[misc]
        new_qty = current + quantity
        if new_qty > product.stock:
            raise ConflictError(
                "Requested quantity exceeds available stock.",
                details={"available": product.stock},
            )
        await self.redis.hset(key, str(product_id), new_qty)  # type: ignore[misc]
        await self._touch_ttl(user_id)
        return await self.get_cart(user_id)

    async def set_item(
        self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int
    ) -> CartResponse:
        product = await self.products.get(product_id)
        if product is None or not product.is_active:
            raise NotFoundError("Product not found or unavailable.")
        if quantity > product.stock:
            raise ConflictError(
                "Requested quantity exceeds available stock.",
                details={"available": product.stock},
            )
        key = self._key(user_id)
        if quantity <= 0:
            await self.redis.hdel(key, str(product_id))  # type: ignore[misc]
        else:
            await self.redis.hset(key, str(product_id), quantity)  # type: ignore[misc]
        await self._touch_ttl(user_id)
        return await self.get_cart(user_id)

    async def remove_item(
        self, user_id: uuid.UUID, product_id: uuid.UUID
    ) -> CartResponse:
        await self.redis.hdel(self._key(user_id), str(product_id))  # type: ignore[misc]
        return await self.get_cart(user_id)

    async def clear(self, user_id: uuid.UUID) -> None:
        await self.redis.delete(self._key(user_id))

    async def get_raw(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        """Return ``{product_id: quantity}`` — used by checkout."""
        raw: dict[str, str] = await self.redis.hgetall(self._key(user_id))  # type: ignore[misc]
        return {uuid.UUID(pid): int(qty) for pid, qty in raw.items()}

    async def get_cart(self, user_id: uuid.UUID) -> CartResponse:
        raw = await self.get_raw(user_id)
        if not raw:
            return CartResponse(
                items=[], total_items=0, subtotal=Decimal("0"), currency="UZS"
            )

        items: list[CartItemResponse] = []
        subtotal = Decimal("0")
        currency = "UZS"
        for product_id, quantity in raw.items():
            product: Product | None = await self.products.get(product_id)
            if product is None or not product.is_active:
                # Stale entry — drop it silently.
                await self.redis.hdel(self._key(user_id), str(product_id))  # type: ignore[misc]
                continue
            line_total = product.price * quantity
            subtotal += line_total
            currency = product.currency
            items.append(
                CartItemResponse(
                    product_id=product.id,
                    name=product.name,
                    slug=product.slug,
                    unit_price=product.price,
                    currency=product.currency,
                    quantity=quantity,
                    line_total=line_total,
                    available_stock=product.stock,
                )
            )
        return CartResponse(
            items=items,
            total_items=sum(i.quantity for i in items),
            subtotal=subtotal,
            currency=currency,
        )
