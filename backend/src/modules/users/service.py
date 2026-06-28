"""User business logic."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.enums import UserRole
from src.core.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
)
from src.core.pagination import Page, PaginationParams
from src.core.security import hash_password, verify_password
from src.modules.users.models import User
from src.modules.users.repository import UserRepository
from src.modules.users.schemas import (
    UserAdminUpdateRequest,
    UserCreateRequest,
    UserStatusUpdateRequest,
    UserUpdateRequest,
)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    async def create(
        self, data: UserCreateRequest, *, role: UserRole = UserRole.CUSTOMER
    ) -> User:
        existing = await self.repo.get_by_email(data.email)
        if existing is not None:
            raise AlreadyExistsError("A user with this email already exists.")
        existing_username = await self.repo.get_by_username(data.username)
        if existing_username is not None:
            raise AlreadyExistsError("A user with this username already exists.")
        return await self.repo.create(
            {
                "email": data.email.lower(),
                "username": data.username.lower(),
                "hashed_password": hash_password(data.password),
                "full_name": data.full_name,
                "phone": data.phone,
                "role": role,
            }
        )

    async def get(self, user_id: uuid.UUID) -> User:
        user = await self.repo.get(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email)

    async def authenticate(self, email_or_username: str, password: str) -> User | None:
        user = await self.repo.get_by_email(email_or_username)

        if user is None:
            user = await self.repo.get_by_username(email_or_username)

        if user is None or not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def list_users(self, params: PaginationParams) -> Page[User]:
        items = await self.repo.get_many(
            offset=params.offset, limit=params.limit, order_by=User.created_at.desc()
        )
        total = await self.repo.count()
        return Page.create(items, total, params)

    async def update_profile(
        self, user: User, data: UserUpdateRequest
    ) -> User:
        return await self.repo.update(
            user, data.model_dump(exclude_unset=True)
        )

    async def admin_update(
        self,
        user_id: uuid.UUID,
        data: UserAdminUpdateRequest | UserStatusUpdateRequest,
    ) -> User:
        user = await self.get(user_id)
        return await self.repo.update(user, data.model_dump(exclude_unset=True))

    async def change_password(
        self, user: User, current: str, new: str
    ) -> None:
        if not verify_password(current, user.hashed_password):
            raise ValidationError("Current password is incorrect.")
        await self.repo.update(user, {"hashed_password": hash_password(new)})

    async def mark_verified(self, user: User) -> User:
        return await self.repo.update(user, {"is_verified": True})

    async def get_or_create_telegram_user(
        self, telegram_id: int, full_name: str | None
    ) -> User:
        """Used by the Telegram auth flow — provisions a passwordless user."""
        user = await self.repo.get_by_telegram_id(telegram_id)
        if user is not None:
            return user
        # Synthetic, unusable password hash — login is via Telegram only.
        placeholder = hash_password(uuid.uuid4().hex)
        username = f"tg_{telegram_id}"
        return await self.repo.create(
            {
                "email": f"{username}@telegram.local",
                "username": username,
                "hashed_password": placeholder,
                "full_name": full_name,
                "telegram_id": telegram_id,
                "role": UserRole.CUSTOMER,
                "is_verified": True,
            }
        )
