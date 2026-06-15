"""Handler routers, aggregated for registration in ``main.py``."""

from __future__ import annotations

from aiogram import Router

from bot.handlers import cart, catalog, checkout, orders, start, support


def get_routers() -> list[Router]:
    """Return all handler routers in registration order."""
    return [
        start.router,
        catalog.router,
        cart.router,
        orders.router,
        checkout.router,
        support.router,
    ]
