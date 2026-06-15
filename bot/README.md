# E-Commerce Telegram Bot (Aiogram3)

Storefront bot that talks to the backend **only** over its REST API (httpx).
No direct database access.

## Setup

```bash
cd bot
cp .env.example .env        # fill in BOT_TOKEN, TELEGRAM_AUTH_SECRET, ...
uv sync --extra dev
```

## Run

From the **repository root** (so `bot` is importable as a package):

```bash
uv run --project bot python -m bot.main
```

* `BOT_ENV=dev`  → long polling (default)
* `BOT_ENV=prod` → webhook (needs `WEBHOOK_BASE_URL`)

With no `BOT_TOKEN` set, the process logs a notice and exits cleanly.

## Layout

| Path                       | Responsibility                                    |
|----------------------------|---------------------------------------------------|
| `config.py`                | Settings from env                                 |
| `services/api_client.py`   | The only gateway to the backend (REST/httpx)      |
| `middlewares/auth.py`      | Per-user Telegram auth + token cache (Redis)      |
| `middlewares/throttling.py`| 30 req/min per user (Redis fixed window)          |
| `states/checkout.py`       | Checkout FSM states                               |
| `keyboards/`               | Inline + reply keyboards and callback factories   |
| `handlers/`                | start, catalog, cart, orders, checkout, support   |
| `main.py`                  | Dispatcher wiring + polling/webhook startup       |
