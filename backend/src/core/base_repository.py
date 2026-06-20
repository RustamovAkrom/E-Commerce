"""Generic async repository base.

Every module repository inherits from ``BaseRepository`` to get the standard
CRUD operations for free. Repositories return ORM models (domain objects);
they never deal with HTTP or Pydantic schemas.
"""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import Base, SoftDeleteMixin

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """CRUD building blocks for a single ORM model.

    Subclasses set the ``model`` class attribute. Soft-delete-aware: if the
    model uses :class:`SoftDeleteMixin`, reads exclude deleted rows and
    ``delete`` performs a soft delete unless ``hard=True``.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @property
    def _soft_delete(self) -> bool:
        return issubclass(self.model, SoftDeleteMixin)

    def _base_select(self) -> Any:
        stmt = select(self.model)
        if self._soft_delete:
            stmt = stmt.where(self.model.is_deleted.is_(False))  # type: ignore[attr-defined]
        return stmt

    async def get(self, id: uuid.UUID) -> ModelT | None:
        stmt = self._base_select().where(self.model.id == id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by(self, **filters: Any) -> ModelT | None:
        stmt = self._base_select().filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_many(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: Any | None = None,
        **filters: Any,
    ) -> list[ModelT]:
        stmt = self._base_select().filter_by(**filters)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_slugs(self, exclude_id: uuid.UUID | None = None) -> set[str]:
        """Return a set of all non-deleted slugs (excluding a specific id if given)."""
        stmt = self._base_select().with_only_columns(self.model.slug)  # type: ignore[attr-defined]
        if exclude_id is not None:
            stmt = stmt.where(self.model.id != exclude_id)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return {row[0] for row in result.all() if row[0]}

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        if self._soft_delete:
            stmt = stmt.where(self.model.is_deleted.is_(False))  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def create(self, data: dict[str, Any]) -> ModelT:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, instance: ModelT, data: dict[str, Any]) -> ModelT:
        for key, value in data.items():
            setattr(instance, key, value)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT, *, hard: bool = False) -> None:
        if self._soft_delete and not hard:
            instance.is_deleted = True  # type: ignore[attr-defined]
            self.session.add(instance)
            await self.session.flush()
        else:
            await self.session.delete(instance)
            await self.session.flush()
