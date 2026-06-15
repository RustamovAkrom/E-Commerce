"""Celery application and shared async-task plumbing.

Celery workers are synchronous, but the platform's services are async. Tasks
therefore run their coroutine via :func:`run_async`, which drives a private
event loop per worker process. Each task opens its own ``AsyncSession`` (the
FastAPI request-scoped session is not available here) and commits explicitly.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Coroutine
from typing import TypeVar

from celery import Celery

from src.config import settings

celery_app = Celery(
    "ecommerce",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    result_expires=3600,
)

# Ensure task modules are imported so their @celery_app.task decorators run.
celery_app.autodiscover_tasks(
    [
        "src.tasks.order_tasks",
        "src.tasks.notification_tasks",
        "src.tasks.report_tasks",
    ]
)

# Periodic schedule (Celery beat). Reports run nightly.
celery_app.conf.beat_schedule = {
    "daily-sales-report": {
        "task": "src.tasks.report_tasks.generate_daily_sales_report",
        "schedule": 60.0 * 60.0 * 24.0,
    },
}

T = TypeVar("T")

_loop: asyncio.AbstractEventLoop | None = None


def _get_loop() -> asyncio.AbstractEventLoop:
    """Return a reusable event loop for this worker process."""
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def run_async(coro: Coroutine[object, object, T] | Awaitable[T]) -> T:
    """Synchronously run an async coroutine inside a Celery task."""
    return _get_loop().run_until_complete(coro)  # type: ignore[arg-type]
