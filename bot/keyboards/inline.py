"""Inline keyboards and their typed callback-data factories.

All callback payloads are modelled with :class:`CallbackData` so handlers can
filter and parse them type-safely instead of hand-splitting strings.
"""

from __future__ import annotations

from typing import Any

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.texts import (
    BTN_ADD_TO_CART,
    BTN_BACK,
    BTN_CHECKOUT,
    BTN_CLEAR_CART,
    BTN_CONTINUE_SHOPPING,
    BTN_NEXT,
    BTN_PREV,
    BTN_REMOVE,
    BTN_VIEW_CART,
    PAYMENT_METHODS,
)


# --- Callback data factories ------------------------------------------------
class CategoryCB(CallbackData, prefix="cat"):
    category_id: str


class ProductsPageCB(CallbackData, prefix="ppage"):
    category_id: str
    page: int


class ProductCB(CallbackData, prefix="prod"):
    slug: str


class CartAddCB(CallbackData, prefix="cadd"):
    product_id: str


class CartRemoveCB(CallbackData, prefix="crem"):
    product_id: str


class CartActionCB(CallbackData, prefix="cact"):
    action: str  # "clear" | "checkout"


class OrderCB(CallbackData, prefix="order"):
    order_id: str


class PaymentCB(CallbackData, prefix="pay"):
    method: str


class NavCB(CallbackData, prefix="nav"):
    to: str  # "catalog" | "cart"


# --- Keyboard builders ------------------------------------------------------
def categories_kb(categories: list[dict[str, Any]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for category in categories:
        builder.button(
            text=category["name"],
            callback_data=CategoryCB(category_id=str(category["id"])),
        )
    builder.adjust(2)
    return builder.as_markup()


def products_kb(
    page: dict[str, Any], category_id: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for product in page["items"]:
        builder.button(
            text=f"{product['name']} — {product['price']} {product['currency']}",
            callback_data=ProductCB(slug=product["slug"]),
        )
    builder.adjust(1)

    current = int(page["page"])
    total = int(page["pages"])
    nav: list[tuple[str, ProductsPageCB]] = []
    if current > 1:
        nav.append((BTN_PREV, ProductsPageCB(category_id=category_id, page=current - 1)))
    if current < total:
        nav.append((BTN_NEXT, ProductsPageCB(category_id=category_id, page=current + 1)))
    if nav:
        nav_builder = InlineKeyboardBuilder()
        for text, cb in nav:
            nav_builder.button(text=text, callback_data=cb)
        nav_builder.adjust(len(nav))
        builder.attach(nav_builder)

    tail = InlineKeyboardBuilder()
    tail.button(text=BTN_VIEW_CART, callback_data=NavCB(to="cart"))
    tail.button(text=BTN_BACK, callback_data=NavCB(to="catalog"))
    tail.adjust(2)
    builder.attach(tail)
    return builder.as_markup()


def product_detail_kb(product: dict[str, Any]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text=BTN_ADD_TO_CART,
        callback_data=CartAddCB(product_id=str(product["id"])),
    )
    builder.button(text=BTN_VIEW_CART, callback_data=NavCB(to="cart"))
    builder.button(
        text=BTN_BACK,
        callback_data=CategoryCB(category_id=str(product["category_id"])),
    )
    builder.adjust(1, 2)
    return builder.as_markup()


def cart_kb(cart: dict[str, Any]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in cart["items"]:
        builder.button(
            text=f"{BTN_REMOVE} {item['name']}",
            callback_data=CartRemoveCB(product_id=str(item["product_id"])),
        )
    builder.adjust(1)

    actions = InlineKeyboardBuilder()
    actions.button(text=BTN_CHECKOUT, callback_data=CartActionCB(action="checkout"))
    actions.button(text=BTN_CLEAR_CART, callback_data=CartActionCB(action="clear"))
    actions.button(text=BTN_CONTINUE_SHOPPING, callback_data=NavCB(to="catalog"))
    actions.adjust(1, 2)
    builder.attach(actions)
    return builder.as_markup()


def orders_kb(orders: list[dict[str, Any]], labels: list[str]) -> InlineKeyboardMarkup:
    """Build a keyboard of order buttons. ``labels`` parallels ``orders``."""
    builder = InlineKeyboardBuilder()
    for order, label in zip(orders, labels, strict=True):
        builder.button(
            text=label, callback_data=OrderCB(order_id=str(order["id"]))
        )
    builder.adjust(1)
    return builder.as_markup()


def payment_methods_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for method, label in PAYMENT_METHODS.items():
        builder.button(text=label, callback_data=PaymentCB(method=method))
    builder.adjust(1)
    return builder.as_markup()


def back_kb(to: str = "catalog") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=BTN_BACK, callback_data=NavCB(to=to))
    return builder.as_markup()
