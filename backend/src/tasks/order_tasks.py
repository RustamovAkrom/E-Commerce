"""Celery tasks for order lifecycle side effects.

These run out-of-band so the HTTP request that triggers them returns quickly.
Each task opens its own session, resolves the order and its owner, and sends
the appropriate customer notification. Tasks are idempotent at the
notification level (a re-delivered task simply sends again / logs again).
"""

from __future__ import annotations

import uuid

from src.core.database import async_session_maker
from src.core.enums import NotificationChannel, NotificationType
from src.modules.notifications.service import NotificationService
from src.modules.orders.repository import OrderRepository
from src.modules.users.repository import UserRepository
from src.tasks.celery_app import celery_app, run_async


def _pick_channel(user_email: str | None, telegram_id: int | None) -> tuple[
    NotificationChannel, str
]:
    """Choose the best channel + destination for a user."""
    if telegram_id:
        return NotificationChannel.TELEGRAM, str(telegram_id)
    return NotificationChannel.EMAIL, user_email or ""


async def _notify_order(
    order_id: uuid.UUID,
    notification_type: NotificationType,
    extra: dict[str, object] | None = None,
) -> str | None:
    async with async_session_maker() as session:
        orders = OrderRepository(session)
        users = UserRepository(session)
        order = await orders.get(order_id)
        if order is None:
            return None
        user = await users.get(order.user_id)
        if user is None:
            return None

        channel, destination = _pick_channel(user.email, user.telegram_id)
        if not destination:
            return None

        context: dict[str, object] = {
            "order_id": str(order.id),
            "full_name": user.full_name or "there",
            "total": f"{order.total_amount}",
            "currency": order.currency,
        }
        if extra:
            context.update(extra)

        notification = await NotificationService(session).send_templated(
            notification_type=notification_type,
            channel=channel,
            destination=destination,
            context=context,
            user_id=user.id,
        )
        await session.commit()
        return str(notification.id)


@celery_app.task(name="src.tasks.order_tasks.send_order_created_notification")
def send_order_created_notification(order_id: str) -> str | None:
    return run_async(
        _notify_order(uuid.UUID(order_id), NotificationType.ORDER_CREATED)
    )


@celery_app.task(name="src.tasks.order_tasks.send_order_paid_notification")
def send_order_paid_notification(order_id: str) -> str | None:
    return run_async(
        _notify_order(uuid.UUID(order_id), NotificationType.ORDER_PAID)
    )


@celery_app.task(name="src.tasks.order_tasks.send_order_shipped_notification")
def send_order_shipped_notification(
    order_id: str, tracking_number: str | None = None
) -> str | None:
    return run_async(
        _notify_order(
            uuid.UUID(order_id),
            NotificationType.ORDER_SHIPPED,
            {"tracking_number": tracking_number or "N/A"},
        )
    )


@celery_app.task(name="src.tasks.order_tasks.send_order_delivered_notification")
def send_order_delivered_notification(order_id: str) -> str | None:
    return run_async(
        _notify_order(uuid.UUID(order_id), NotificationType.ORDER_DELIVERED)
    )
