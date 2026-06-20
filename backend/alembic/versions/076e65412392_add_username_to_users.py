"""add_username_to_users

Revision ID: 076e65412392
Revises: 2f4b9a7c1d3e
Create Date: 2026-06-19 18:01:02.445006+00:00
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '076e65412392'
down_revision: str | None = '2f4b9a7c1d3e'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
