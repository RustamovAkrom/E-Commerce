"""add delivery tables

Revision ID: 2f4b9a7c1d3e
Revises: d4a3f3ae0ee0
Create Date: 2026-06-19 16:58:00.000000+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2f4b9a7c1d3e"
down_revision: str | None = "d4a3f3ae0ee0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "couriers",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("zone", sa.String(length=128), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("couriers", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_couriers_is_deleted"), ["is_deleted"], unique=False)
        batch_op.create_index(batch_op.f("ix_couriers_user_id"), ["user_id"], unique=True)
        batch_op.create_index(batch_op.f("ix_couriers_zone"), ["zone"], unique=False)

    op.create_table(
        "delivery_assignments",
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("courier_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "PICKED_UP",
                "IN_TRANSIT",
                "DELIVERED",
                "FAILED",
                "CANCELLED",
                name="deliverystatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["courier_id"], ["couriers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("delivery_assignments", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_delivery_assignments_courier_id"), ["courier_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_delivery_assignments_order_id"), ["order_id"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_delivery_assignments_status"), ["status"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("delivery_assignments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_delivery_assignments_status"))
        batch_op.drop_index(batch_op.f("ix_delivery_assignments_order_id"))
        batch_op.drop_index(batch_op.f("ix_delivery_assignments_courier_id"))

    op.drop_table("delivery_assignments")
    with op.batch_alter_table("couriers", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_couriers_zone"))
        batch_op.drop_index(batch_op.f("ix_couriers_user_id"))
        batch_op.drop_index(batch_op.f("ix_couriers_is_deleted"))

    op.drop_table("couriers")
