"""Support handler — forwards a user's message to the admin chat."""

from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.config import settings
from bot.texts import (
    BTN_CART,
    BTN_CATALOG,
    BTN_ORDERS,
    BTN_SUPPORT,
    SUPPORT_FORWARD_HEADER,
    SUPPORT_NOT_CONFIGURED,
    SUPPORT_PROMPT,
    SUPPORT_SENT,
)

router = Router(name="support")

_MENU_BUTTONS = {BTN_CATALOG, BTN_CART, BTN_ORDERS, BTN_SUPPORT}


class SupportStates(StatesGroup):
    waiting_message = State()


@router.message(Command("support"))
@router.message(F.text == BTN_SUPPORT)
async def support_entry(message: Message, state: FSMContext) -> None:
    await state.set_state(SupportStates.waiting_message)
    await message.answer(SUPPORT_PROMPT)


@router.message(SupportStates.waiting_message, F.text & ~F.text.in_(_MENU_BUTTONS))
async def forward_to_admin(
    message: Message, state: FSMContext, bot: Bot
) -> None:
    await state.clear()
    if not settings.ADMIN_CHAT_ID:
        await message.answer(SUPPORT_NOT_CONFIGURED)
        return
    user = message.from_user
    body = SUPPORT_FORWARD_HEADER.format(
        user=user.full_name if user else "unknown",
        user_id=user.id if user else 0,
        text=message.text or "",
    )
    await bot.send_message(settings.ADMIN_CHAT_ID, body)
    await message.answer(SUPPORT_SENT)
