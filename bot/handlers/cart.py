"""Cart handlers: view, add, remove, clear."""

from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.keyboards.inline import (
    CartActionCB,
    CartAddCB,
    CartRemoveCB,
    NavCB,
    cart_kb,
)
from bot.services.api_client import AsyncAPIClient
from bot.texts import (
    BTN_CART,
    CART_CLEARED,
    CART_EMPTY,
    CART_ITEM_ADDED,
    CART_ITEM_REMOVED,
    CART_LINE,
    CART_TITLE,
    CART_TOTAL,
)

router = Router(name="cart")


def _render_cart(cart: dict[str, Any]) -> tuple[str, InlineKeyboardMarkup | None]:
    if not cart["items"]:
        return CART_EMPTY, None
    lines = [CART_TITLE]
    for item in cart["items"]:
        lines.append(
            CART_LINE.format(
                name=item["name"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
                line_total=item["line_total"],
                currency=item["currency"],
            )
        )
    lines.append(
        CART_TOTAL.format(
            subtotal=cart["subtotal"],
            currency=cart["currency"],
            total_items=cart["total_items"],
        )
    )
    return "\n".join(lines), cart_kb(cart)


@router.message(F.text == BTN_CART)
async def open_cart(message: Message, api: AsyncAPIClient) -> None:
    text, kb = _render_cart(await api.get_cart())
    await message.answer(text, reply_markup=kb)


@router.callback_query(NavCB.filter(F.to == "cart"))
async def open_cart_cb(callback: CallbackQuery, api: AsyncAPIClient) -> None:
    text, kb = _render_cart(await api.get_cart())
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(CartAddCB.filter())
async def add_item(
    callback: CallbackQuery, callback_data: CartAddCB, api: AsyncAPIClient
) -> None:
    await api.add_to_cart(callback_data.product_id, 1)
    await callback.answer(CART_ITEM_ADDED)


@router.callback_query(CartRemoveCB.filter())
async def remove_item(
    callback: CallbackQuery, callback_data: CartRemoveCB, api: AsyncAPIClient
) -> None:
    cart = await api.remove_from_cart(callback_data.product_id)
    text, kb = _render_cart(cart)
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer(CART_ITEM_REMOVED)


@router.callback_query(CartActionCB.filter(F.action == "clear"))
async def clear_cart(callback: CallbackQuery, api: AsyncAPIClient) -> None:
    await api.clear_cart()
    if isinstance(callback.message, Message):
        await callback.message.edit_text(CART_EMPTY)
    await callback.answer(CART_CLEARED)
