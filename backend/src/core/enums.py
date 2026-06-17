"""Cross-module enums.

Kept in ``core`` so that ``dependencies.py`` and module models can share the
same definitions without importing each other (avoids circular imports).
"""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    OPERATOR = "operator"
    VENDOR = "vendor"
    COURIER = "courier"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentProvider(StrEnum):
    CLICK = "click"
    PAYME = "payme"
    STRIPE = "stripe"


class NotificationChannel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"


class NotificationType(StrEnum):
    ORDER_CREATED = "order_created"
    ORDER_PAID = "order_paid"
    ORDER_SHIPPED = "order_shipped"
    ORDER_DELIVERED = "order_delivered"
    PAYMENT_FAILED = "payment_failed"
    ACCOUNT_VERIFIED = "account_verified"
    GENERIC = "generic"


# Role ranking used for hierarchical permission checks.
ROLE_RANK: dict[UserRole, int] = {
    UserRole.CUSTOMER: 0,
    UserRole.VENDOR: 1,
    UserRole.COURIER: 1,
    UserRole.OPERATOR: 2,
    UserRole.ADMIN: 3,
    UserRole.SUPERADMIN: 4,
}
