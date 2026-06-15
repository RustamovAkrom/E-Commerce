"""Generic notification dispatch tasks.

Allows any part of the system (or an admin action) to fan a notification out
to a channel asynchronously. The HTTP path can enqueue ``send_notification``
instead of awaiting delivery inline.
"""

from __future__ import annotations

import uuid

from src.core.database import async_session_maker
from src.core.enums import NotificationChannel, NotificationType
from src.modules.notifications.schemas import NotificationSendRequest
from src.modules.notifications.service import NotificationService
from src.tasks.celery_app import celery_app, run_async


async def _send(
    *,
    channel: str,
    destination: str,
    subject: str | None,
    body: str,
    user_id: str | None,
    notification_type: str,
) -> str:
    async with async_session_maker() as session:
        request = NotificationSendRequest(
            user_id=uuid.UUID(user_id) if user_id else None,
            type=NotificationType(notification_type),
            channel=NotificationChannel(channel),
            destination=destination,
            subject=subject,
            body=body,
        )
        notification = await NotificationService(session).send(request)
        await session.commit()
        return str(notification.id)


@celery_app.task(
    name="src.tasks.notification_tasks.send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_notification(
    self,  # noqa: ANN001 - Celery bound task instance
    *,
    channel: str,
    destination: str,
    body: str,
    subject: str | None = None,
    user_id: str | None = None,
    notification_type: str = NotificationType.GENERIC.value,
) -> str:
    return run_async(
        _send(
            channel=channel,
            destination=destination,
            subject=subject,
            body=body,
            user_id=user_id,
            notification_type=notification_type,
        )
    )
