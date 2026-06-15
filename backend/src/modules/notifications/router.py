"""Notification HTTP endpoints.

Customer: read own notification inbox. Admin: dispatch an ad-hoc notification
over any channel.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import CurrentUser, DbSession, require_admin
from src.core.pagination import Page, PaginationParams
from src.modules.notifications.schemas import (
    NotificationResponse,
    NotificationSendRequest,
)
from src.modules.notifications.service import NotificationService

router = APIRouter()


@router.get("", response_model=Page[NotificationResponse])
async def list_my_notifications(
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
    params: Annotated[PaginationParams, Depends()],
) -> Page[NotificationResponse]:
    page = await NotificationService(db).list_for_user(user.id, params)  # type: ignore[attr-defined]
    return page.map(NotificationResponse.model_validate)


@router.post(
    "/send",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def send_notification(
    data: NotificationSendRequest,
    db: DbSession,
) -> NotificationResponse:
    notification = await NotificationService(db).send(data)
    return NotificationResponse.model_validate(notification)
