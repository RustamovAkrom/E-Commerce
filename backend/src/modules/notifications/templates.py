"""Notification message templates.

Maps a :class:`NotificationType` to a subject/body pair rendered from a context
dict. Kept declarative and dependency-free so both the service and Celery tasks
can render without extra wiring. Unknown keys in the context are ignored;
missing keys fall back to a sensible placeholder.
"""

from __future__ import annotations

from collections import defaultdict

from src.core.enums import NotificationType

# (subject, body) templates using ``str.format_map`` placeholders.
_TEMPLATES: dict[NotificationType, tuple[str, str]] = {
    NotificationType.ORDER_CREATED: (
        "Order {order_id} received",
        "Hi {full_name}, we've received your order {order_id} "
        "for {total} {currency}. We'll let you know when it ships.",
    ),
    NotificationType.ORDER_PAID: (
        "Payment confirmed for order {order_id}",
        "Thank you {full_name}! Your payment of {total} {currency} for order "
        "{order_id} was successful.",
    ),
    NotificationType.ORDER_SHIPPED: (
        "Order {order_id} has shipped",
        "Good news {full_name} — order {order_id} is on its way. "
        "Tracking: {tracking_number}.",
    ),
    NotificationType.ORDER_DELIVERED: (
        "Order {order_id} delivered",
        "Your order {order_id} has been delivered. We hope you enjoy it, "
        "{full_name}!",
    ),
    NotificationType.PAYMENT_FAILED: (
        "Payment failed for order {order_id}",
        "Hi {full_name}, your payment for order {order_id} could not be "
        "processed. Please try again.",
    ),
    NotificationType.ACCOUNT_VERIFIED: (
        "Your account is verified",
        "Welcome aboard {full_name}! Your account has been verified.",
    ),
    NotificationType.GENERIC: (
        "{subject}",
        "{body}",
    ),
}


def render(
    notification_type: NotificationType, context: dict[str, object]
) -> tuple[str, str]:
    """Return ``(subject, body)`` for ``notification_type`` and ``context``."""
    subject_tpl, body_tpl = _TEMPLATES.get(
        notification_type, _TEMPLATES[NotificationType.GENERIC]
    )
    # Missing placeholders render as an empty string rather than raising.
    safe_context: dict[str, object] = defaultdict(str, context)
    subject = subject_tpl.format_map(safe_context)
    body = body_tpl.format_map(safe_context)
    return subject, body
