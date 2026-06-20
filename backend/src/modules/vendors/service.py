"""Vendor business logic (marketplace mode).

A user applies to become a vendor; the application starts in ``PENDING`` and an
admin approves, suspends or rejects it. Approving a vendor also promotes the
owning user to the ``VENDOR`` role so RBAC-gated vendor endpoints unlock.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    AlreadyExistsError,
    NotFoundError,
)
from src.core.pagination import Page, PaginationParams
from src.core.utils import generate_slug
from src.modules.users.repository import UserRepository
from src.modules.vendors.models import Vendor, VendorStatus
from src.modules.vendors.repository import VendorRepository
from src.modules.vendors.schemas import (
    VendorAdminUpdateRequest,
    VendorApplyRequest,
    VendorUpdateRequest,
)


class VendorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = VendorRepository(session)
        self.users = UserRepository(session)

    async def apply(
        self, user_id: uuid.UUID, data: VendorApplyRequest
    ) -> Vendor:
        if await self.repo.get_by_user(user_id) is not None:
            raise AlreadyExistsError("You already have a vendor account.")
        return await self.repo.create(
            {
                "user_id": user_id,
                "name": data.name,
                "slug": generate_slug(data.name, await self.repo.get_all_slugs()),
                "description": data.description,
                "contact_email": data.contact_email,
                "contact_phone": data.contact_phone,
                "status": VendorStatus.PENDING,
            }
        )

    async def get(self, vendor_id: uuid.UUID) -> Vendor:
        vendor = await self.repo.get(vendor_id)
        if vendor is None:
            raise NotFoundError("Vendor not found.")
        return vendor

    async def get_by_slug(self, slug: str) -> Vendor:
        vendor = await self.repo.get_by_slug(slug)
        if vendor is None:
            raise NotFoundError("Vendor not found.")
        return vendor

    async def get_my_vendor(self, user_id: uuid.UUID) -> Vendor:
        vendor = await self.repo.get_by_user(user_id)
        if vendor is None:
            raise NotFoundError("You do not have a vendor account.")
        return vendor

    async def update_my_vendor(
        self, user_id: uuid.UUID, data: VendorUpdateRequest
    ) -> Vendor:
        vendor = await self.get_my_vendor(user_id)
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload:
            payload["slug"] = generate_slug(
                payload["name"], await self.repo.get_all_slugs(exclude_id=vendor.id)
            )
        return await self.repo.update(vendor, payload)

    async def list_public(self, params: PaginationParams) -> Page[Vendor]:
        items, total = await self.repo.list_public(
            offset=params.offset, limit=params.limit
        )
        return Page.create(items, total, params)

    # --- Admin --------------------------------------------------------------
    async def list_all(self, params: PaginationParams) -> Page[Vendor]:
        items, total = await self.repo.list_all(
            offset=params.offset, limit=params.limit
        )
        return Page.create(items, total, params)

    async def admin_update(
        self, vendor_id: uuid.UUID, data: VendorAdminUpdateRequest
    ) -> Vendor:
        vendor = await self.get(vendor_id)
        payload = data.model_dump(exclude_unset=True)
        new_status = payload.get("status")
        vendor = await self.repo.update(vendor, payload)
        # Approving a vendor promotes the owner to the VENDOR role.
        if new_status == VendorStatus.APPROVED:
            owner = await self.users.get(vendor.user_id)
            if owner is not None and owner.role == UserRole.CUSTOMER:
                await self.users.update(owner, {"role": UserRole.VENDOR})
        return vendor

    async def approve(self, vendor_id: uuid.UUID) -> Vendor:
        return await self.admin_update(
            vendor_id, VendorAdminUpdateRequest(status=VendorStatus.APPROVED)
        )

    async def delete(self, vendor_id: uuid.UUID) -> None:
        vendor = await self.get(vendor_id)
        await self.repo.delete(vendor)
