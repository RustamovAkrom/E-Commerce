"""Order status state machine.

Centralises the legal status transitions so the order service never has to
hard-code them. Raising :class:`ConflictError` on an illegal transition keeps
the state graph authoritative.
"""

from __future__ import annotations

from src.core.enums import OrderStatus
from src.core.exceptions import ConflictError

# Allowed transitions: current status -> set of permissible next statuses.
_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {
        OrderStatus.CONFIRMED,
        OrderStatus.PAID,
        OrderStatus.CANCELLED,
    },
    OrderStatus.CONFIRMED: {
        OrderStatus.PAID,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAID: {
        OrderStatus.PROCESSING,
        OrderStatus.REFUNDED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PROCESSING: {
        OrderStatus.SHIPPED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.SHIPPED: {
        OrderStatus.DELIVERED,
    },
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
    OrderStatus.REFUNDED: set(),
}

# Statuses from which a customer may cancel their own order.
CUSTOMER_CANCELLABLE = {OrderStatus.PENDING, OrderStatus.CONFIRMED}

# Terminal statuses that release reserved stock back to inventory.
STOCK_RELEASING = {OrderStatus.CANCELLED}


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in _TRANSITIONS.get(current, set())


def ensure_transition(current: OrderStatus, target: OrderStatus) -> None:
    """Raise if ``current -> target`` is not a legal transition."""
    if not can_transition(current, target):
        raise ConflictError(
            f"Cannot transition order from {current.value} to {target.value}.",
            details={
                "current": current.value,
                "target": target.value,
                "allowed": [s.value for s in _TRANSITIONS.get(current, set())],
            },
        )
