"""Admin dashboard aggregation logic.

Read-only cross-module reporting that does not belong to any single feature
module. Queries are written directly here (rather than fanning out to each
module repository) because they are dashboard-specific aggregates.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    DashboardStats,
    OrderStatusBreakdown,
    RevenuePoint,
    SalesOverview,
)
from src.core.enums import OrderStatus
from src.modules.catalog.models import Product
from src.modules.orders.models import Order
from src.modules.users.models import User

# Stock at or below this threshold flags a product as "low stock".
_LOW_STOCK_THRESHOLD = 5

# Order statuses representing realised revenue.
_REVENUE_STATUSES = (
    OrderStatus.PAID,
    OrderStatus.PROCESSING,
    OrderStatus.SHIPPED,
    OrderStatus.DELIVERED,
)


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _scalar_int(self, stmt: object) -> int:
        return int((await self.session.execute(stmt)).scalar_one())  # type: ignore[arg-type]

    async def dashboard(self) -> DashboardStats:
        total_users = await self._scalar_int(
            select(func.count(User.id)).where(User.is_deleted.is_(False))
        )
        total_products = await self._scalar_int(
            select(func.count(Product.id)).where(Product.is_deleted.is_(False))
        )
        active_products = await self._scalar_int(
            select(func.count(Product.id)).where(
                Product.is_deleted.is_(False),
                Product.is_active.is_(True),
            )
        )
        total_orders = await self._scalar_int(
            select(func.count(Order.id)).where(Order.is_deleted.is_(False))
        )
        pending_orders = await self._scalar_int(
            select(func.count(Order.id)).where(
                Order.is_deleted.is_(False),
                Order.status == OrderStatus.PENDING,
            )
        )
        low_stock = await self._scalar_int(
            select(func.count(Product.id)).where(
                Product.is_deleted.is_(False),
                Product.is_active.is_(True),
                Product.stock <= _LOW_STOCK_THRESHOLD,
            )
        )
        revenue = (
            await self.session.execute(
                select(
                    func.coalesce(func.sum(Order.total_amount), Decimal("0"))
                ).where(
                    Order.is_deleted.is_(False),
                    Order.status.in_(_REVENUE_STATUSES),
                )
            )
        ).scalar_one()

        return DashboardStats(
            total_users=total_users,
            total_products=total_products,
            active_products=active_products,
            total_orders=total_orders,
            total_revenue=Decimal(revenue),
            pending_orders=pending_orders,
            low_stock_products=low_stock,
        )

    async def order_status_breakdown(self) -> list[OrderStatusBreakdown]:
        stmt = (
            select(Order.status, func.count(Order.id))
            .where(Order.is_deleted.is_(False))
            .group_by(Order.status)
        )
        rows = (await self.session.execute(stmt)).all()
        return [
            OrderStatusBreakdown(status=status, count=int(count))
            for status, count in rows
        ]

    async def sales_overview(self, days: int = 30) -> SalesOverview:
        now = datetime.now(UTC)
        end = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            days=1
        )
        start = end - timedelta(days=days)

        # Per-day revenue, portable across SQLite/PostgreSQL via func.date().
        day = func.date(Order.created_at)
        stmt = (
            select(
                day.label("day"),
                func.count(Order.id),
                func.coalesce(func.sum(Order.total_amount), Decimal("0")),
            )
            .where(
                Order.is_deleted.is_(False),
                Order.status.in_(_REVENUE_STATUSES),
                Order.created_at >= start,
                Order.created_at < end,
            )
            .group_by(day)
            .order_by(day)
        )
        rows = (await self.session.execute(stmt)).all()

        points = [
            RevenuePoint(
                date=str(d),
                order_count=int(count),
                revenue=Decimal(revenue),
            )
            for d, count, revenue in rows
        ]
        total_revenue = sum((p.revenue for p in points), Decimal("0"))
        order_count = sum(p.order_count for p in points)
        return SalesOverview(
            period_days=days,
            total_revenue=total_revenue,
            order_count=order_count,
            points=points,
        )
