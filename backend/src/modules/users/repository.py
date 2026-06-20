"""User repository — DB queries only."""

from __future__ import annotations

from src.core.base_repository import BaseRepository
from src.modules.users.models import User


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        return await self.get_by(email=email.lower())

    async def get_by_username(self, username: str) -> User | None:
        return await self.get_by(username=username)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.get_by(telegram_id=telegram_id)
