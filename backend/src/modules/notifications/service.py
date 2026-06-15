"""Notification business logic.

Dispatches a message over a channel, persisting an audit row with the delivery
outcome. Two entry points:

* :meth:`send` — caller supplies a fully-rendered subject/body.
* :meth:`send_templated` — caller supplies a :class:`NotificationType` and a
  context dict; the body is rendered from the template registry.

Delivery never raises: a failed send is recorded with ``status=FAILED`` and the
error message, so the calling order/payment flow is not derailed by a flaky
mail server.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import NotificationChannel, NotificationType
from src.core.pagination import Page, PaginationParams
from src.modules.notifications.channels import get_channel
from src.modules.notifications.models import Notification, NotificationStatus
from src.modules.notifications.repository import NotificationRepository
from src.modules.notifications.schemas import NotificationSendRequest
from src.modules.notifications.templates import render


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = NotificationRepository(session)

    async def send(self, data: NotificationSendRequest) -> Notification:
        return await self._dispatch(
            user_id=data.user_id,
            notification_type=data.type,
            channel=data.channel,
            destination=data.destination,
            subject=data.subject,
            body=data.body,
            payload=data.payload,
        )

    async def send_templated(
        self,
        *,
        notification_type: NotificationType,
        channel: NotificationChannel,
        destination: str,
        context: dict[str, object],
        user_id: uuid.UUID | None = None,
    ) -> Notification:
        subject, body = render(notification_type, context)
        return await self._dispatch(
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            destination=destination,
            subject=subject,
            body=body,
            payload=context,
        )

    async def _dispatch(
        self,
        *,
        user_id: uuid.UUID | None,
        notification_type: NotificationType,
        channel: NotificationChannel,
        destination: str,
        subject: str | None,
        body: str,
        payload: dict[str, object],
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            type=notification_type,
            channel=channel,
            status=NotificationStatus.PENDING,
            destination=destination,
            subject=subject,
            body=body,
            payload=dict(payload),
        )
        self.session.add(notification)
        await self.session.flush()

        result = await get_channel(channel).send(
            destination=destination, subject=subject, body=body
        )
        notification.status = (
            NotificationStatus.SENT if result.success else NotificationStatus.FAILED
        )
        notification.error = None if result.success else result.detail
        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)
        return notification

    async def list_for_user(
        self, user_id: uuid.UUID, params: PaginationParams
    ) -> Page[Notification]:
        items, total = await self.repo.list_for_user(
            user_id, offset=params.offset, limit=params.limit
        )
        return Page.create(items, total, params)
