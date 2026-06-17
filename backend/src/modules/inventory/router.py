"""Inventory HTTP endpoints (admin-only writes, stock reads)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from src.core.dependencies import DbSession, require_role
from src.core.enums import UserRole
from src.modules.inventory.schemas import (
    StockAdjustRequest,
    StockLevelResponse,
)
from src.modules.inventory.service import InventoryService

router = APIRouter()


@router.get("/{product_id}", response_model=StockLevelResponse)
async def get_stock_level(
    product_id: uuid.UUID, db: DbSession
) -> StockLevelResponse:
    level = await InventoryService(db).get_level(product_id)
    return StockLevelResponse(product_id=product_id, stock=level)


@router.post(
    "/adjust",
    response_model=StockLevelResponse,
    dependencies=[Depends(require_role(UserRole.OPERATOR, UserRole.ADMIN, UserRole.SUPERADMIN))],
)
async def adjust_stock(
    data: StockAdjustRequest, db: DbSession
) -> StockLevelResponse:
    new_level = await InventoryService(db).adjust(data)
    return StockLevelResponse(product_id=data.product_id, stock=new_level)
