"""/start handler — greets the user and shows the main menu.

User provisioning with the backend happens transparently in AuthMiddleware,
so by the time this runs the user already has a backend session.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.reply import main_menu_kb
from bot.texts import WELCOME

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()  # drop any half-finished flow
    await message.answer(WELCOME, reply_markup=main_menu_kb())
