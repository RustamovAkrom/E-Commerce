"""Checkout flow FSM states."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    """Steps of the checkout conversation."""

    waiting_address = State()
    waiting_phone = State()
    waiting_payment_method = State()
