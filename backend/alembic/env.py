"""Alembic environment — async, driven by application settings."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from alembic.autogenerate.api import AutogenContext
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.types import TypeEngine
from src.config import settings
from src.models_registry import Base  # noqa: F401  (registers all models)

config = context.config

# Inject the runtime DB URL (escape % for configparser interpolation).
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def render_item(
    type_: str, obj: object, autogen_context: AutogenContext
) -> str | bool:
    """Custom autogenerate rendering.

    ``JSONB`` carries an implicit ``astext_type=Text()``. Alembic renders that
    inner ``Text()`` unqualified, which produces an ``F821 undefined name``
    (and a migration that fails to import). When a column's type involves JSONB
    — directly or through a ``with_variant`` mapping — make ``Text`` importable
    in the generated migration so the rendered ``Text()`` resolves.
    """
    if type_ == "type" and isinstance(obj, TypeEngine):
        variant_mapping = getattr(obj, "_variant_mapping", None) or {}
        involves_jsonb = isinstance(obj, postgresql.JSONB) or any(
            isinstance(variant, postgresql.JSONB)
            for variant in variant_mapping.values()
        )
        if involves_jsonb:
            autogen_context.imports.add("from sqlalchemy import Text")
    return False  # fall back to alembic's default rendering


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_item=render_item,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_item=render_item,
        render_as_batch=settings.is_sqlite,  # batch mode for SQLite ALTER support
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
