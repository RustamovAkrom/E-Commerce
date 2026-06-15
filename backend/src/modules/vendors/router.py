"""Vendor HTTP endpoints (mounted only when ``MARKETPLACE_MODE`` is on).

Public: browse approved vendors. Authenticated user: apply to become a vendor,
read/update own storefront. Admin: list all, moderate, delete.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import CurrentUser, DbSession, require_admin
from src.core.pagination import Page, PaginationParams
from src.core.schemas import MessageResponse
from src.modules.vendors.schemas import (
    VendorAdminUpdateRequest,
    VendorApplyRequest,
    VendorPublicResponse,
    VendorResponse,
    VendorUpdateRequest,
)
from src.modules.vendors.service import VendorService

router = APIRouter()


# --- Public -----------------------------------------------------------------
@router.get("", response_model=Page[VendorPublicResponse])
async def list_vendors(
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
) -> Page[VendorPublicResponse]:
    page = await VendorService(db).list_public(params)
    return page.map(VendorPublicResponse.model_validate)


@router.get("/slug/{slug}", response_model=VendorPublicResponse)
async def get_vendor_by_slug(
    slug: str,
    db: DbSession,
) -> VendorPublicResponse:
    vendor = await VendorService(db).get_by_slug(slug)
    return VendorPublicResponse.model_validate(vendor)


# --- Authenticated user: own storefront ------------------------------------
@router.post(
    "/apply",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_as_vendor(
    data: VendorApplyRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> VendorResponse:
    vendor = await VendorService(db).apply(user.id, data)  # type: ignore[attr-defined]
    return VendorResponse.model_validate(vendor)


@router.get("/me", response_model=VendorResponse)
async def get_my_vendor(
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> VendorResponse:
    vendor = await VendorService(db).get_my_vendor(user.id)  # type: ignore[attr-defined]
    return VendorResponse.model_validate(vendor)


@router.patch("/me", response_model=VendorResponse)
async def update_my_vendor(
    data: VendorUpdateRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> VendorResponse:
    vendor = await VendorService(db).update_my_vendor(user.id, data)  # type: ignore[attr-defined]
    return VendorResponse.model_validate(vendor)


# --- Admin ------------------------------------------------------------------
@router.get(
    "/admin/all",
    response_model=Page[VendorResponse],
    dependencies=[Depends(require_admin)],
)
async def list_all_vendors(
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
) -> Page[VendorResponse]:
    page = await VendorService(db).list_all(params)
    return page.map(VendorResponse.model_validate)


@router.get(
    "/{vendor_id}",
    response_model=VendorResponse,
    dependencies=[Depends(require_admin)],
)
async def get_vendor(
    vendor_id: uuid.UUID,
    db: DbSession,
) -> VendorResponse:
    vendor = await VendorService(db).get(vendor_id)
    return VendorResponse.model_validate(vendor)


@router.patch(
    "/{vendor_id}",
    response_model=VendorResponse,
    dependencies=[Depends(require_admin)],
)
async def admin_update_vendor(
    vendor_id: uuid.UUID,
    data: VendorAdminUpdateRequest,
    db: DbSession,
) -> VendorResponse:
    vendor = await VendorService(db).admin_update(vendor_id, data)
    return VendorResponse.model_validate(vendor)


@router.delete(
    "/{vendor_id}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
async def delete_vendor(
    vendor_id: uuid.UUID,
    db: DbSession,
) -> MessageResponse:
    await VendorService(db).delete(vendor_id)
    return MessageResponse(message="Vendor deleted.")
