"""Add agent session memory tables for SDK SQLAlchemySession.

Mirrors the table definitions in
agents/extensions/memory/sqlalchemy_session.py so the session can run with
create_tables=False.

Also serves as the merge point for the two pre-existing heads
(b2c3d4e5f6a7 recreated tool_call_timeline; c3d4e5f6a7b8 drops it, matching
the current ORM which has no timeline model).

Revision ID: e5f6a7b8c9d0
Revises: b2c3d4e5f6a7, c3d4e5f6a7b8
Create Date: 2026-07-02 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = ("b2c3d4e5f6a7", "c3d4e5f6a7b8")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_sessions",
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("message_data", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=False),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["agent_sessions.session_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_agent_messages_session_time",
        "agent_messages",
        ["session_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_agent_messages_session_time", table_name="agent_messages")
    op.drop_table("agent_messages")
    op.drop_table("agent_sessions")
