"""Admin dashboard Pydantic schemas."""

from __future__ import annotations

from decimal import Decimal

from src.core.enums import OrderStatus
from src.core.schemas import StrictSchema


class DashboardStats(StrictSchema):
    """Top-line counts for the admin home screen."""

    total_users: int
    total_products: int
    active_products: int
    total_orders: int
    total_revenue: Decimal
    pending_orders: int
    low_stock_products: int


class OrderStatusBreakdown(StrictSchema):
    """Order counts grouped by status."""

    status: OrderStatus
    count: int


class RevenuePoint(StrictSchema):
    """A single day's revenue for the sales chart."""

    date: str
    order_count: int
    revenue: Decimal


class SalesOverview(StrictSchema):
    period_days: int
    total_revenue: Decimal
    order_count: int
    points: list[RevenuePoint]
