"""Recreate tool_call_timeline table after orphaned migration dropped it.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-30 22:18:33.164102
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tool_call_timeline",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("turn_id", sa.UUID(), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("group_name", sa.String(length=100), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("visible_args_json", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["turn_id"], ["conversation_turns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_timeline_turn_seq",
        "tool_call_timeline",
        ["turn_id", "sequence_no"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_timeline_turn_seq", table_name="tool_call_timeline")
    op.drop_table("tool_call_timeline")
