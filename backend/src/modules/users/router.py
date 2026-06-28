"""User HTTP endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.core.dependencies import (
    CurrentUser,
    DbSession,
    require_admin,
    require_superadmin,
)
from src.core.exceptions import ValidationError
from src.core.pagination import Page, PaginationParams
from src.core.schemas import MessageResponse
from src.modules.users.schemas import (
    PasswordChangeRequest,
    UserAdminUpdateRequest,
    UserResponse,
    UserStatusUpdateRequest,
    UserUpdateRequest,
)
from src.modules.users.service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_me(user: CurrentUser) -> UserResponse:  # type: ignore[valid-type]
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdateRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> UserResponse:
    updated = await UserService(db).update_profile(user, data)  # type: ignore[arg-type]
    return UserResponse.model_validate(updated)


@router.post(
    "/me/password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def change_password(
    data: PasswordChangeRequest,
    db: DbSession,
    user: CurrentUser,  # type: ignore[valid-type]
) -> MessageResponse:
    await UserService(db).change_password(
        user,  # type: ignore[arg-type]
        data.current_password,
        data.new_password,
    )
    return MessageResponse(message="Password updated.")


# --- Admin endpoints --------------------------------------------------------
@router.get(
    "",
    response_model=Page[UserResponse],
    dependencies=[Depends(require_admin)],
)
async def list_users(
    db: DbSession,
    params: Annotated[PaginationParams, Depends()],
) -> Page[UserResponse]:
    page = await UserService(db).list_users(params)
    return page.map(UserResponse.model_validate)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
async def get_user(user_id: uuid.UUID, db: DbSession) -> UserResponse:
    user = await UserService(db).get(user_id)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
async def admin_update_user(
    user_id: uuid.UUID,
    data: UserStatusUpdateRequest,
    db: DbSession,
) -> UserResponse:
    """ADMIN+ can update activation/verification — but NOT role."""
    user = await UserService(db).admin_update(user_id, data)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(require_superadmin)],
)
async def update_user_role(
    user_id: uuid.UUID,
    data: UserAdminUpdateRequest,
    db: DbSession,
) -> UserResponse:
    """Only SUPERADMIN can change user roles."""
    user = await UserService(db).admin_update(user_id, data)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    dependencies=[Depends(require_admin)],
)
async def toggle_user_status(
    user_id: uuid.UUID,
    data: UserStatusUpdateRequest,
    db: DbSession,
) -> UserResponse:
    """ADMIN+ can activate/deactivate users."""
    if data.is_active is None:
        raise ValidationError("is_active field is required.")
    user = await UserService(db).admin_update(user_id, data)
    return UserResponse.model_validate(user)
