"""Drop tool call timeline table.

Revision ID: c3d4e5f6a7b8
Revises: 9f3e7df3a2c1
Create Date: 2026-07-01 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "9f3e7df3a2c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("idx_timeline_turn_seq", table_name="tool_call_timeline")
    op.drop_table("tool_call_timeline")


def downgrade() -> None:
    op.create_table(
        "tool_call_timeline",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("group_name", sa.String(length=100), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("visible_args_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["turn_id"], ["conversation_turns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_timeline_turn_seq",
        "tool_call_timeline",
        ["turn_id", "sequence_no"],
        unique=False,
    )
