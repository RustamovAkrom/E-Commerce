"""Redis-backed shopping cart.

The cart is a Redis hash keyed ``cart:{user_id}`` mapping
``product_id -> quantity``. Product details and prices are resolved live from
the catalog when the cart is read, so price/stock are always current.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import cast

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.exceptions import CacheError, ConflictError, NotFoundError
from src.modules.cart.schemas import CartItemResponse, CartResponse
from src.modules.catalog.models import Product
from src.modules.catalog.repository import ProductRepository


class CartService:
    def __init__(self, session: AsyncSession, redis_client: redis.Redis) -> None:
        self.session = session
        self.redis = redis_client
        self.products = ProductRepository(session)

    async def _handle_redis_error(self, operation: str) -> None:
        """Raise CacheError for Redis failures with context."""
        raise CacheError(
            f"Cart operation failed: {operation}",
            details={"operation": operation},
        )

    @staticmethod
    def _key(user_id: uuid.UUID) -> str:
        return f"cart:{user_id}"

    async def _touch_ttl(self, user_id: uuid.UUID) -> None:
        try:
            await self.redis.expire(self._key(user_id), settings.CART_TTL_SECONDS)
        except redis.RedisError as e:
            await self._handle_redis_error(f"expire TTL for user {user_id}: {e}")

    async def add_item(
        self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int
    ) -> CartResponse:
        product = await self.products.get(product_id)
        if product is None or not product.is_active:
            raise NotFoundError("Product not found or unavailable.")

        # Check currency consistency with existing cart items
        raw = await self.get_raw(user_id)
        if raw:
            for existing_product_id in raw.keys():
                if existing_product_id != product_id:
                    existing_product = await self.products.get(existing_product_id)
                    if existing_product and existing_product.currency != product.currency:
                        raise ConflictError(
                            "Cannot add product with different currency to cart.",
                            details={
                                "existing_currency": existing_product.currency,
                                "new_currency": product.currency,
                            },
                        )

        key = self._key(user_id)
        try:
            current_str = await self.redis.hget(key, str(product_id))
        except redis.RedisError as e:
            await self._handle_redis_error(f"get cart item for user {user_id}: {e}")
        
        current = int(cast(str | bytes | None, current_str) or 0)
        new_qty = current + quantity
        if new_qty > product.stock:
            raise ConflictError(
                "Requested quantity exceeds available stock.",
                details={"available": product.stock},
            )
        
        try:
            await self.redis.hset(key, str(product_id), new_qty)
        except redis.RedisError as e:
            await self._handle_redis_error(f"set cart item for user {user_id}: {e}")
        
        await self._touch_ttl(user_id)
        return await self.get_cart(user_id)

    async def set_item(
        self, user_id: uuid.UUID, product_id: uuid.UUID, quantity: int
    ) -> CartResponse:
        product = await self.products.get(product_id)
        if product is None or not product.is_active:
            raise NotFoundError("Product not found or unavailable.")
        
        # Check currency consistency with existing cart items (only if adding/updating)
        if quantity > 0:
            raw = await self.get_raw(user_id)
            if raw:
                for existing_product_id in raw.keys():
                    if existing_product_id != product_id:
                        existing_product = await self.products.get(existing_product_id)
                        if existing_product and existing_product.currency != product.currency:
                            raise ConflictError(
                                "Cannot set product with different currency to cart.",
                                details={
                                    "existing_currency": existing_product.currency,
                                    "new_currency": product.currency,
                                },
                            )
        
        if quantity > product.stock:
            raise ConflictError(
                "Requested quantity exceeds available stock.",
                details={"available": product.stock},
            )
        key = self._key(user_id)
        try:
            if quantity <= 0:
                await self.redis.hdel(key, str(product_id))
            else:
                await self.redis.hset(key, str(product_id), quantity)
        except redis.RedisError as e:
            await self._handle_redis_error(f"set cart item for user {user_id}: {e}")
        
        await self._touch_ttl(user_id)
        return await self.get_cart(user_id)

    async def remove_item(
        self, user_id: uuid.UUID, product_id: uuid.UUID
    ) -> CartResponse:
        try:
            await self.redis.hdel(self._key(user_id), str(product_id))
        except redis.RedisError as e:
            await self._handle_redis_error(f"remove cart item for user {user_id}: {e}")
        return await self.get_cart(user_id)

    async def clear(self, user_id: uuid.UUID) -> None:
        try:
            await self.redis.delete(self._key(user_id))
        except redis.RedisError as e:
            await self._handle_redis_error(f"clear cart for user {user_id}: {e}")

    async def get_raw(self, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        """Return ``{product_id: quantity}`` — used by checkout."""
        try:
            raw: dict[str | bytes, str | bytes] = await self.redis.hgetall(self._key(user_id))
        except redis.RedisError as e:
            await self._handle_redis_error(f"get cart for user {user_id}: {e}")
        
        return {
            uuid.UUID(str(pid)): int(qty)
            for pid, qty in raw.items()
        }

    async def get_cart(self, user_id: uuid.UUID) -> CartResponse:
        raw = await self.get_raw(user_id)
        if not raw:
            return CartResponse(
                items=[], total_items=0, subtotal=Decimal("0"), currency="UZS"
            )

        items: list[CartItemResponse] = []
        subtotal = Decimal("0")
        currency: str | None = None
        
        for product_id, quantity in raw.items():
            product: Product | None = await self.products.get(product_id)
            if product is None or not product.is_active:
                # Stale entry — drop it silently.
                try:
                    await self.redis.hdel(self._key(user_id), str(product_id))
                except redis.RedisError:
                    # Ignore errors when cleaning up stale entries
                    pass
                continue
            
            # Validate currency consistency
            if currency is None:
                currency = product.currency
            elif product.currency != currency:
                raise ConflictError(
                    "Cart cannot contain products with different currencies.",
                    details={
                        "expected_currency": currency,
                        "product_currency": product.currency,
                        "product_name": product.name,
                    },
                )
            
            line_total = product.price * quantity
            subtotal += line_total
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
        
        # If all products were stale/inactive
        if not items:
            return CartResponse(
                items=[], total_items=0, subtotal=Decimal("0"), currency="UZS"
            )
        
        return CartResponse(
            items=items,
            total_items=sum(i.quantity for i in items),
            subtotal=subtotal,
            currency=currency or "UZS",
        )
