"""Use pgvector column and index for chunk embedding retrieval.

Revision ID: 9f3e7df3a2c1
Revises: d4c0865a4138
Create Date: 2026-02-25 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f3e7df3a2c1"
down_revision: str | Sequence[str] | None = "d4c0865a4138"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Migrate embeddings from JSON to pgvector and add ANN index."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        ALTER TABLE chunk_embeddings
        ALTER COLUMN embedding TYPE vector(3072)
        USING (embedding::text::vector(3072))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chunk_embeddings_embedding_hnsw
        ON chunk_embeddings
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    """Revert embeddings from pgvector back to JSON."""
    op.execute("DROP INDEX IF EXISTS idx_chunk_embeddings_embedding_hnsw")
    op.execute(
        """
        ALTER TABLE chunk_embeddings
        ALTER COLUMN embedding TYPE json
        USING (to_json(embedding::float4[]))
        """
    )
