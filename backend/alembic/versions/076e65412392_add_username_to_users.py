"""add_username_to_users

Revision ID: 076e65412392
Revises: 2f4b9a7c1d3e
Create Date: 2026-06-19 18:01:02.445006+00:00

Adds the ``username`` column to ``users``: a 64-char, unique, indexed,
NOT NULL column. Existing rows are backfilled from the local part of their
email (``john@x.com`` -> ``john``), with a numeric suffix appended on collision
so the unique index can be created safely. Written idempotently so it can be
re-applied on a database where a previous (empty) version of this migration was
already stamped.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '076e65412392'
down_revision: str | None = '2f4b9a7c1d3e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add the column nullable first so existing rows don't violate NOT NULL.
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(64)"
    )

    # 2. Backfill from the email local part, de-duplicating with a row-number
    #    suffix so the unique index below can be created. Truncated to 64 chars.
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                LOWER(SPLIT_PART(email, '@', 1)) AS base,
                ROW_NUMBER() OVER (
                    PARTITION BY LOWER(SPLIT_PART(email, '@', 1))
                    ORDER BY created_at, id
                ) AS rn
            FROM users
            WHERE username IS NULL OR username = ''
        )
        UPDATE users u
        SET username = LEFT(
            CASE WHEN r.rn = 1 THEN r.base
                 ELSE r.base || '_' || r.rn::text
            END,
            64
        )
        FROM ranked r
        WHERE u.id = r.id
        """
    )

    # 3. Any rows still empty (e.g. email had no local part) get a fallback.
    op.execute(
        "UPDATE users SET username = 'user_' || LEFT(id::text, 8) "
        "WHERE username IS NULL OR username = ''"
    )

    # 4. Enforce NOT NULL now that every row has a value.
    op.alter_column(
        "users",
        "username",
        existing_type=sa.String(length=64),
        nullable=False,
    )

    # 5. Unique index (matches the model's index=True, unique=True).
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username "
        "ON users (username)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_username")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS username")
