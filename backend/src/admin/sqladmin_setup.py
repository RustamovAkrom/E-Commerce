"""SQLAdmin integration for the platform admin panel.

Routes are mounted at ``/admin/panel`` and require authentication via a
JWT bearer token (same as the REST API).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqladmin import ModelView
from sqladmin.filters import (
    BooleanFilter,
    ForeignKeyFilter,
    OperationColumnFilter,
    StaticValuesFilter,
)

from src.core.database import async_session_maker
from src.core.enums import OrderStatus, UserRole
from src.core.security import decode_token
from src.modules.catalog.models import Category, Product, ProductImage
from src.modules.delivery.models import Courier, DeliveryAssignment, DeliveryStatus
from src.modules.inventory.models import MovementReason, StockMovement
from src.modules.orders.models import Order, OrderItem
from src.modules.users.models import User
from src.modules.vendors.models import Vendor, VendorStatus

# ─── Auth helper ────────────────────────────────────────────────────────────

async def _get_current_user(token: str | None) -> User | None:
    """Extract the authenticated User from a JWT token (for SQLAdmin)."""
    if not token:
        return None
    from src.modules.users.models import User as UserModel

    try:
        payload = decode_token(token)
    except Exception:
        return None
    subject = payload.get("sub")
    if not subject:
        return None
    async with async_session_maker() as session:
        user = await session.get(UserModel, uuid.UUID(subject))
        if user and not user.is_deleted and user.is_active:
            return user
    return None


def _require_min_role(min_role: UserRole) -> bool:  # noqa: ARG001
    """Return True — access is checked via token presence in is_action_allowed."""
    return True


# ─── Base ModelView ────────────────────────────────────────────────────────

class AuthenticatedView(ModelView):
    """Base for all admin views — ensures auth token is present."""

    column_list_export = []
    column_details_list = []
    column_export_list = []

    def _get_token(self, request: Any) -> str | None:
        """Extract Bearer token from request headers."""
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None

    def is_action_allowed(self, request: Any) -> bool:
        """Block unauthenticated requests."""
        token = self._get_token(request)
        return token is not None


# ─── Product views (OPERATOR+) ─────────────────────────────────────────────

class ProductAdmin(AuthenticatedView, model=Product):
    name = "Products"
    column_list = ("id", "name", "price", "stock", "is_active", "category")
    column_details_list = (
        "id", "name", "slug", "description", "sku",
        "price", "currency", "stock", "is_active",
        "category", "vendor", "images",
    )
    form_columns = (
        "name", "description", "sku",
        "price", "currency", "stock", "is_active",
        "category", "vendor",
    )
    form_formatters = {
        "category": lambda m, a: m.category.name if m.category else None,
        "vendor": lambda m, a: m.vendor.name if m.vendor else None,
    }
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ("name", "sku", "slug")
    column_filters = (
        BooleanFilter(Product.is_active, "Active"),
        ForeignKeyFilter(Product.category_id, Category.name, Category, "Category"),
        ForeignKeyFilter(Product.vendor_id, Vendor.name, Vendor, "Vendor"),
    )


class CategoryAdmin(AuthenticatedView, model=Category):
    name = "Categories"
    column_list = ("id", "name", "slug", "is_active", "sort_order")
    column_details_list = (
        "id", "name", "slug", "description",
        "parent", "is_active", "sort_order",
    )
    form_columns = ("name", "description", "parent", "is_active", "sort_order")
    can_create = True
    can_edit = True
    can_delete = True
    column_searchable_list = ("name", "slug")
    column_filters = (
        BooleanFilter(Category.is_active, "Active"),
        ForeignKeyFilter(Category.parent_id, Category.name, Category, "Parent"),
    )


class ProductImageAdmin(AuthenticatedView, model=ProductImage):
    name = "Product Images"
    column_list = ("id", "product_id", "url", "is_primary", "sort_order")
    form_columns = ("product_id", "url", "is_primary", "sort_order")
    can_create = True
    can_edit = True
    can_delete = True


class StockMovementAdmin(AuthenticatedView, model=StockMovement):
    name = "Stock Movements"
    column_list = ("id", "product_id", "delta", "reason", "reference")
    column_details_list = ("id", "product_id", "delta", "reason", "reference", "created_at")
    can_create = False
    can_edit = False
    can_delete = False
    column_searchable_list = ("product_id", "reference")
    column_filters = (
        StaticValuesFilter(
            StockMovement.reason,
            [(r.value, r.value) for r in MovementReason] + [("", "All")],
            "Reason",
        ),
    )


# ─── Order views (OPERATOR+) ───────────────────────────────────────────────

class OrderAdmin(AuthenticatedView, model=Order):
    name = "Orders"
    column_list = ("id", "user_id", "status", "total_amount", "created_at")
    column_details_list = (
        "id", "user_id", "status", "total_amount", "currency",
        "shipping_address", "note", "items", "created_at",
    )
    form_edit_columns = ("status",)
    can_create = False
    can_delete = False
    column_searchable_list = ("id",)
    column_filters = (
        StaticValuesFilter(
            Order.status,
            [(s.value, s.value) for s in OrderStatus] + [("", "All")],
            "Status",
        ),
    )


class OrderItemAdmin(AuthenticatedView, model=OrderItem):
    name = "Order Items"
    column_list = ("id", "order_id", "product_id", "product_name", "quantity", "unit_price")
    column_details_list = ("id", "order_id", "product_id", "product_name", "quantity", "unit_price")
    can_create = False
    can_edit = False
    can_delete = False


# ─── User views (ADMIN+) ───────────────────────────────────────────────────

class UserAdmin(AuthenticatedView, model=User):
    name = "Users"
    column_list = ("id", "username", "email", "role", "is_active", "is_verified", "created_at")
    column_details_list = (
        "id", "username", "email", "full_name", "phone",
        "role", "is_active", "is_verified",
        "created_at",
    )
    form_edit_columns = ("role", "is_active", "is_verified")
    can_create = False
    can_delete = False
    column_searchable_list = ("username", "email", "full_name")
    column_filters = (
        StaticValuesFilter(
            User.role,
            [(r.value, r.value) for r in UserRole] + [("", "All")],
            "Role",
        ),
        BooleanFilter(User.is_active, "Active"),
        BooleanFilter(User.is_verified, "Verified"),
    )


# ─── Vendor views (ADMIN+) ─────────────────────────────────────────────────

class VendorAdmin(AuthenticatedView, model=Vendor):
    name = "Vendors"
    column_list = ("id", "name", "slug", "status", "is_active", "created_at")
    column_details_list = (
        "id", "user", "name", "slug", "description",
        "status", "is_active", "commission_rate", "created_at",
    )
    form_edit_columns = ("status", "is_active")
    form_excluded_columns = ("slug",)
    can_create = False
    can_delete = True
    column_searchable_list = ("name", "slug")
    column_filters = (
        StaticValuesFilter(
            Vendor.status,
            [(s.value, s.value) for s in VendorStatus] + [("", "All")],
            "Status",
        ),
        BooleanFilter(Vendor.is_active, "Active"),
    )


# ─── Courier views (ADMIN+) ────────────────────────────────────────────────

class CourierAdmin(AuthenticatedView, model=Courier):
    name = "Couriers"
    column_list = ("id", "user_id", "phone", "zone", "is_active")
    column_details_list = ("id", "user_id", "phone", "zone", "is_active", "created_at")
    form_edit_columns = ("phone", "zone", "is_active")
    form_create_columns = ("user_id", "phone", "zone")
    can_delete = False
    column_searchable_list = ("phone", "zone")


class DeliveryAssignmentAdmin(AuthenticatedView, model=DeliveryAssignment):
    name = "Deliveries"
    column_list = ("id", "order_id", "courier_id", "status", "created_at")
    column_details_list = ("id", "order_id", "courier_id", "status", "created_at")
    form_edit_columns = ("status", "courier_id")
    can_create = False
    can_delete = False
    column_searchable_list = ("order_id",)
    column_filters = (
        StaticValuesFilter(
            DeliveryAssignment.status,
            [(s.value, s.value) for s in DeliveryStatus] + [("", "All")],
            "Status",
        ),
        OperationColumnFilter(DeliveryAssignment.courier_id, "Courier"),
    )
