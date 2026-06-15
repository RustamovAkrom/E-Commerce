"""Reporting tasks.

A nightly job (scheduled via Celery beat in :mod:`celery_app`) aggregates the
previous day's paid orders into a sales summary. The result is returned (and
stored in the Celery result backend); an on-demand variant accepts an explicit
date range. Pure read-only aggregation — no mutations.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select

from src.core.database import async_session_maker
from src.core.enums import OrderStatus
from src.modules.orders.models import Order
from src.tasks.celery_app import celery_app, run_async

# Order statuses that represent realised revenue.
_REVENUE_STATUSES = (
    OrderStatus.PAID,
    OrderStatus.PROCESSING,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
)


async def _sales_report(start: datetime, end: datetime) -> dict[str, object]:
    async with async_session_maker() as session:
        stmt = select(
            func.count(Order.id),
            func.coalesce(func.sum(Order.total_amount), Decimal("0")),
        ).where(
            Order.is_deleted.is_(False),
            Order.status.in_(_REVENUE_STATUSES),
            Order.created_at >= start,
            Order.created_at < end,
        )
        order_count, revenue = (await session.execute(stmt)).one()

        # Top products by quantity require a join through order_items; kept
        # simple here as an aggregate count to avoid an expensive query nightly.
        return {
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "order_count": int(order_count),
            "revenue": str(revenue),
        }


@celery_app.task(name="src.tasks.report_tasks.generate_daily_sales_report")
def generate_daily_sales_report() -> dict[str, object]:
    """Aggregate yesterday's revenue. Scheduled nightly via Celery beat."""
    now = datetime.now(UTC)
    end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=1)
    return run_async(_sales_report(start, end))


@celery_app.task(name="src.tasks.report_tasks.generate_sales_report")
def generate_sales_report(start_iso: str, end_iso: str) -> dict[str, object]:
    """On-demand sales report for an explicit ``[start, end)`` ISO range."""
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    return run_async(_sales_report(start, end))
