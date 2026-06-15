"""Admin dashboard HTTP endpoints.

All endpoints are gated behind the ``require_admin`` RBAC guard. They expose
read-only aggregates for the admin panel; per-resource admin CRUD lives on each
module's own router (e.g. ``/orders/admin/all``).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.admin.schemas import (
    DashboardStats,
    OrderStatusBreakdown,
    SalesOverview,
)
from src.admin.service import AdminService
from src.core.dependencies import DbSession, require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(db: DbSession) -> DashboardStats:
    return await AdminService(db).dashboard()


@router.get(
    "/orders/status-breakdown",
    response_model=list[OrderStatusBreakdown],
)
async def order_status_breakdown(db: DbSession) -> list[OrderStatusBreakdown]:
    return await AdminService(db).order_status_breakdown()


@router.get("/sales/overview", response_model=SalesOverview)
async def sales_overview(
    db: DbSession,
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> SalesOverview:
    return await AdminService(db).sales_overview(days)
