"""Restore planner_model_used column name on conversation_turns.

Revision ID: a1b2c3d4e5f6
Revises: 9f3e7df3a2c1
Create Date: 2026-06-30 19:56:32.587830
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "9f3e7df3a2c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'conversation_turns'
            AND column_name = 'model_used'
        ) AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'conversation_turns'
            AND column_name = 'planner_model_used'
        ) THEN
            ALTER TABLE conversation_turns
            RENAME COLUMN model_used TO planner_model_used;
        END IF;
    END $$;
    """)


def downgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'conversation_turns'
            AND column_name = 'planner_model_used'
        ) AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'conversation_turns'
            AND column_name = 'model_used'
        ) THEN
            ALTER TABLE conversation_turns
            RENAME COLUMN planner_model_used TO model_used;
        END IF;
    END $$;
    """)
