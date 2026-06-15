"""Bot entry point.

Wires the dispatcher (Redis FSM storage, middlewares, routers, error handler)
and starts it in the right mode:

* ``BOT_ENV=dev``  -> long polling
* ``BOT_ENV=prod`` -> webhook served by an aiohttp web server

Run with: ``uv run python -m bot.main`` (from the repository root).
"""

from __future__ import annotations

import asyncio
import logging

import redis.asyncio as redis
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import CallbackQuery, ErrorEvent, Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import settings
from bot.handlers import get_routers
from bot.middlewares import AuthMiddleware, ThrottlingMiddleware
from bot.services.api_client import APIError
from bot.texts import GENERIC_ERROR, SERVICE_UNAVAILABLE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("bot")


def create_bot() -> Bot:
    """Construct the Bot with sane defaults (HTML parse mode)."""
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher() -> Dispatcher:
    """Build a fully-wired Dispatcher (no network I/O performed here)."""
    storage = RedisStorage.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=storage)

    # A dedicated Redis client for the middlewares (token cache + throttling).
    middleware_redis: redis.Redis = redis.Redis.from_url(
        settings.REDIS_URL, decode_responses=True
    )

    throttling = ThrottlingMiddleware(
        middleware_redis,
        limit=settings.THROTTLE_LIMIT,
        window=settings.THROTTLE_WINDOW,
    )
    auth = AuthMiddleware(
        settings.BACKEND_API_URL,
        settings.TELEGRAM_AUTH_SECRET,
        middleware_redis,
        token_ttl=settings.ACCESS_TOKEN_CACHE_TTL,
        request_timeout=settings.REQUEST_TIMEOUT,
    )

    # Throttle first (outer), then authenticate — on both messages and callbacks.
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(throttling)
        observer.outer_middleware(auth)

    for router in get_routers():
        dp.include_router(router)

    _register_error_handler(dp)
    return dp


def _register_error_handler(dp: Dispatcher) -> None:
    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        exc = event.exception
        logger.exception("Update handling failed: %s", exc)
        text = SERVICE_UNAVAILABLE if isinstance(exc, APIError) else GENERIC_ERROR

        update = event.update
        message: Message | None = update.message
        callback: CallbackQuery | None = update.callback_query
        try:
            if message is not None:
                await message.answer(text)
            elif callback is not None:
                await callback.answer(text, show_alert=True)
        except Exception:  # noqa: BLE001 -- never let the handler itself crash
            logger.warning("Failed to deliver error notice to user")
        return True  # mark as handled


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    logger.info("Starting in polling mode (dev)")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def run_webhook(bot: Bot, dp: Dispatcher) -> None:
    logger.info("Starting in webhook mode (prod): %s", settings.webhook_url)
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.WEBHOOK_SECRET or None,
        drop_pending_updates=True,
    )
    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.WEBHOOK_SECRET or None,
    ).register(app, path=settings.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner, host=settings.WEB_SERVER_HOST, port=settings.WEB_SERVER_PORT
    )
    await site.start()
    # Serve until cancelled.
    await asyncio.Event().wait()


async def main() -> None:
    if not settings.BOT_TOKEN:
        logger.warning(
            "BOT_TOKEN is not set - nothing to start. "
            "Set BOT_TOKEN in bot/.env to run the bot."
        )
        return

    bot = create_bot()
    dp = build_dispatcher()
    try:
        if settings.is_prod:
            await run_webhook(bot, dp)
        else:
            await run_polling(bot, dp)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
