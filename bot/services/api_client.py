"""Async REST client for the backend API.

Every call the bot makes to the backend goes through this class. It wraps
``httpx.AsyncClient`` and normalises transport/HTTP errors into a single
:class:`APIError` that the global error handler can catch and turn into a
friendly "service unavailable" reply.

The bot never touches the database — this client is the entire data layer.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx

# Backend route fragments (kept here so handlers stay free of URL strings).
_AUTH_TELEGRAM = "/api/v1/auth/telegram"
_CATEGORIES = "/api/v1/catalog/categories"
_PRODUCTS = "/api/v1/catalog/products"
_PRODUCT_BY_SLUG = "/api/v1/catalog/products/slug/{slug}"
_CART = "/api/v1/cart"
_CART_ITEMS = "/api/v1/cart/items"
_CART_ITEM = "/api/v1/cart/items/{product_id}"
_ORDERS = "/api/v1/orders"
_ORDER = "/api/v1/orders/{order_id}"

JSON = dict[str, Any]


class APIError(Exception):
    """Raised for any backend transport or non-2xx response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AsyncAPIClient:
    """Thin async wrapper over the backend REST API.

    Create an *anonymous* client (no token) for the Telegram auth handshake,
    or an *authenticated* client (``token=...``) for cart/order endpoints.
    """

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        auth_secret: str = "",
        timeout: float = 15.0,
    ) -> None:
        self._auth_secret = auth_secret
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout,
        )

    # --- lifecycle ----------------------------------------------------------
    async def __aenter__(self) -> AsyncAPIClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    # --- low-level request --------------------------------------------------
    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, path, **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise APIError(
                f"Backend returned {exc.response.status_code} for {path}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.HTTPError as exc:
            raise APIError(f"Request to {path} failed: {exc}") from exc

        if response.status_code == httpx.codes.NO_CONTENT or not response.content:
            return None
        return response.json()

    # --- auth ---------------------------------------------------------------
    async def register_telegram_user(
        self, telegram_id: int, username: str | None, full_name: str | None
    ) -> JSON:
        """Provision/login a Telegram user; returns the token pair.

        Returns the backend ``TokenPair`` dict: ``access_token``,
        ``refresh_token``, ``token_type``, ``expires_in``.
        """
        payload = {
            "telegram_id": telegram_id,
            "full_name": full_name or username,
            "auth_secret": self._auth_secret,
        }
        result: JSON = await self._request("POST", _AUTH_TELEGRAM, json=payload)
        return result["tokens"]

    # --- catalog ------------------------------------------------------------
    async def get_categories(self) -> list[JSON]:
        result: list[JSON] = await self._request("GET", _CATEGORIES)
        return result

    async def get_products(
        self,
        category_id: str | None = None,
        page: int = 1,
        size: int = 6,
    ) -> JSON:
        params: JSON = {"page": page, "size": size}
        if category_id:
            params["category_id"] = category_id
        result: JSON = await self._request("GET", _PRODUCTS, params=params)
        return result

    async def get_product(self, slug: str) -> JSON:
        result: JSON = await self._request(
            "GET", _PRODUCT_BY_SLUG.format(slug=slug)
        )
        return result

    # --- cart ---------------------------------------------------------------
    async def get_cart(self) -> JSON:
        result: JSON = await self._request("GET", _CART)
        return result

    async def add_to_cart(self, product_id: str, qty: int = 1) -> JSON:
        result: JSON = await self._request(
            "POST",
            _CART_ITEMS,
            json={"product_id": product_id, "quantity": qty},
        )
        return result

    async def remove_from_cart(self, product_id: str) -> JSON:
        result: JSON = await self._request(
            "DELETE", _CART_ITEM.format(product_id=product_id)
        )
        return result

    async def clear_cart(self) -> JSON:
        result: JSON = await self._request("DELETE", _CART)
        return result

    # --- orders -------------------------------------------------------------
    async def create_order(
        self, address: JSON, note: str | None = None
    ) -> JSON:
        payload: JSON = {"shipping_address": address, "note": note}
        result: JSON = await self._request("POST", _ORDERS, json=payload)
        return result

    async def get_orders(self, page: int = 1, size: int = 10) -> JSON:
        result: JSON = await self._request(
            "GET", _ORDERS, params={"page": page, "size": size}
        )
        return result

    async def get_order(self, order_id: str) -> JSON:
        result: JSON = await self._request(
            "GET", _ORDER.format(order_id=order_id)
        )
        return result
