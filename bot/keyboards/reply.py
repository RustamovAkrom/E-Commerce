"""Reply (persistent) keyboards."""

from __future__ import annotations

from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.texts import BTN_CART, BTN_CATALOG, BTN_ORDERS, BTN_SUPPORT


def main_menu_kb() -> ReplyKeyboardMarkup:
    """The always-visible bottom menu: Catalog / Cart / Orders / Support."""
    builder = ReplyKeyboardBuilder()
    builder.button(text=BTN_CATALOG)
    builder.button(text=BTN_CART)
    builder.button(text=BTN_ORDERS)
    builder.button(text=BTN_SUPPORT)
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True, is_persistent=True)
