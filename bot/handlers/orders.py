"""Order handlers: list the user's orders and show order details."""

from __future__ import annotations

from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import OrderCB, orders_kb
from bot.services.api_client import AsyncAPIClient
from bot.texts import (
    BTN_ORDERS,
    NO_ORDERS,
    ORDER_BUTTON,
    ORDER_DETAIL,
    ORDER_ITEM_LINE,
    ORDERS_TITLE,
    STATUS_EMOJI,
)

router = Router(name="orders")


def _short(order_id: str) -> str:
    return str(order_id)[:8]


def _button_label(order: dict[str, Any]) -> str:
    status = order["status"]
    return ORDER_BUTTON.format(
        emoji=STATUS_EMOJI.get(status, ""),
        short_id=_short(order["id"]),
        total=order["total_amount"],
        currency=order["currency"],
    )


@router.message(F.text == BTN_ORDERS)
async def list_orders(message: Message, api: AsyncAPIClient) -> None:
    page = await api.get_orders()
    orders = page["items"]
    if not orders:
        await message.answer(NO_ORDERS)
        return
    labels = [_button_label(order) for order in orders]
    await message.answer(ORDERS_TITLE, reply_markup=orders_kb(orders, labels))


@router.callback_query(OrderCB.filter())
async def order_detail(
    callback: CallbackQuery, callback_data: OrderCB, api: AsyncAPIClient
) -> None:
    order = await api.get_order(callback_data.order_id)
    items = "\n".join(
        ORDER_ITEM_LINE.format(
            name=item["product_name"],
            quantity=item["quantity"],
            unit_price=item["unit_price"],
        )
        for item in order["items"]
    )
    status = order["status"]
    text = ORDER_DETAIL.format(
        short_id=_short(order["id"]),
        emoji=STATUS_EMOJI.get(status, ""),
        status=status,
        total=order["total_amount"],
        currency=order["currency"],
        created_at=str(order["created_at"])[:10],
        items=items or "—",
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text)
    await callback.answer()
