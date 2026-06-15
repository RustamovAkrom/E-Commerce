"""Checkout FSM: address -> phone -> payment method -> create order."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import CartActionCB, PaymentCB, payment_methods_kb
from bot.keyboards.reply import main_menu_kb
from bot.services.api_client import AsyncAPIClient
from bot.states.checkout import CheckoutStates
from bot.texts import (
    BTN_CART,
    BTN_CATALOG,
    BTN_ORDERS,
    BTN_SUPPORT,
    CHECKOUT_ASK_ADDRESS,
    CHECKOUT_ASK_PAYMENT,
    CHECKOUT_ASK_PHONE,
    CHECKOUT_EMPTY_CART,
    CHECKOUT_INVALID_ADDRESS,
    CHECKOUT_INVALID_PHONE,
    ORDER_CREATED,
    PAYMENT_METHODS,
)

router = Router(name="checkout")

_MENU_BUTTONS = {BTN_CATALOG, BTN_CART, BTN_ORDERS, BTN_SUPPORT}
_MIN_ADDRESS_LEN = 5
_MIN_PHONE_LEN = 5
_DEFAULT_CITY = "—"


@router.callback_query(CartActionCB.filter(F.action == "checkout"))
async def start_checkout(
    callback: CallbackQuery, api: AsyncAPIClient, state: FSMContext
) -> None:
    cart = await api.get_cart()
    if not cart["items"]:
        await callback.answer(CHECKOUT_EMPTY_CART, show_alert=True)
        return
    await state.set_state(CheckoutStates.waiting_address)
    if isinstance(callback.message, Message):
        await callback.message.answer(CHECKOUT_ASK_ADDRESS)
    await callback.answer()


@router.message(Command("cancel"), StateFilter(CheckoutStates))
async def cancel_checkout(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Checkout cancelled.", reply_markup=main_menu_kb())


@router.message(
    CheckoutStates.waiting_address, F.text & ~F.text.in_(_MENU_BUTTONS)
)
async def enter_address(message: Message, state: FSMContext) -> None:
    address = (message.text or "").strip()
    if len(address) < _MIN_ADDRESS_LEN:
        await message.answer(CHECKOUT_INVALID_ADDRESS)
        return
    await state.update_data(address=address)
    await state.set_state(CheckoutStates.waiting_phone)
    await message.answer(CHECKOUT_ASK_PHONE)


@router.message(
    CheckoutStates.waiting_phone, F.text & ~F.text.in_(_MENU_BUTTONS)
)
async def enter_phone(message: Message, state: FSMContext) -> None:
    phone = (message.text or "").strip()
    if len(phone) < _MIN_PHONE_LEN:
        await message.answer(CHECKOUT_INVALID_PHONE)
        return
    await state.update_data(phone=phone)
    await state.set_state(CheckoutStates.waiting_payment_method)
    await message.answer(CHECKOUT_ASK_PAYMENT, reply_markup=payment_methods_kb())


@router.callback_query(
    CheckoutStates.waiting_payment_method, PaymentCB.filter()
)
async def choose_payment(
    callback: CallbackQuery,
    callback_data: PaymentCB,
    api: AsyncAPIClient,
    state: FSMContext,
) -> None:
    data = await state.get_data()
    method_label = PAYMENT_METHODS.get(callback_data.method, callback_data.method)
    full_name = callback.from_user.full_name if callback.from_user else "Customer"
    address = {
        "full_name": full_name or "Customer",
        "phone": data["phone"],
        "address": data["address"],
        "city": _DEFAULT_CITY,
        "country": "UZ",
    }
    order = await api.create_order(
        address, note=f"Payment method: {method_label}"
    )
    await state.clear()
    text = ORDER_CREATED.format(
        order_id=str(order["id"])[:8],
        status=order["status"],
        total=order["total_amount"],
        currency=order["currency"],
        payment=method_label,
    )
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text)
    await callback.answer()
