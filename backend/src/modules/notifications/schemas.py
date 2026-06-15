"""Notification Pydantic schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from src.core.enums import NotificationChannel, NotificationType
from src.core.schemas import ORMSchema, StrictSchema
from src.modules.notifications.models import NotificationStatus


class NotificationSendRequest(StrictSchema):
    """Admin / internal request to dispatch a notification."""

    user_id: uuid.UUID | None = None
    type: NotificationType = NotificationType.GENERIC
    channel: NotificationChannel
    destination: str = Field(min_length=1, max_length=255)
    subject: str | None = Field(default=None, max_length=255)
    body: str = Field(min_length=1)
    payload: dict = Field(default_factory=dict)


class NotificationResponse(ORMSchema):
    id: uuid.UUID
    user_id: uuid.UUID | None
    type: NotificationType
    channel: NotificationChannel
    status: NotificationStatus
    destination: str
    subject: str | None
    body: str
    error: str | None
    created_at: datetime
