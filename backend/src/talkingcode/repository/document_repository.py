"""Document repository."""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.domain.models import RetrievedChunk
from talkingcode.enums import Area, FileType
from talkingcode.models.orm import ChunkEmbedding, Document, DocumentChunk


@dataclass(slots=True)
class DocumentRepository:
    """Repository for document operations."""
    
    session: AsyncSession
    
    async def search_chunks(
        self,
        query_embedding: list[float],
        filters: dict[str, Any],
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """Search chunks by similarity."""
        # Simplified: return empty list for now (real implementation would use pgvector)
        # In production, use: SELECT ... ORDER BY embedding <-> query_embedding LIMIT top_k
        return []
    
    async def get_file_details(
        self,
        repo: str,
        path: str,
        ref: str | None = None,
    ) -> dict[str, Any] | None:
        """Get file details from cache."""
        result = await self.session.execute(
            select(Document)
            .join(Document.repository)
            .where(
                Document.path == path,
                Document.git_ref == (ref or "main"),
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            return None
        
        return {
            "repo": repo,
            "path": path,
            "summary": f"Document at {path}",
            "symbols": document.symbols_json or [],
        }
    
    async def save_document(
        self,
        repository_id: UUID,
        path: str,
        content_sha: str,
        git_ref: str,
        classification: dict[str, Any],
    ) -> UUID:
        """Save or update document."""
        from sqlalchemy.dialects.postgresql import insert
        
        stmt = insert(Document).values(
            repository_id=repository_id,
            path=path,
            git_ref=git_ref,
            content_sha=content_sha,
            language=classification.get("language", ""),
            area=classification.get("area", Area.UNKNOWN.value),
            file_type=classification.get("file_type", FileType.UNKNOWN.value),
            symbols_json=classification.get("symbols", []),
            tags_json=classification.get("tags", []),
        ).on_conflict_do_update(
            index_elements=["repository_id", "path", "git_ref"],
            set_={
                "content_sha": content_sha,
                "language": classification.get("language", ""),
                "area": classification.get("area", Area.UNKNOWN.value),
                "file_type": classification.get("file_type", FileType.UNKNOWN.value),
                "symbols_json": classification.get("symbols", []),
                "tags_json": classification.get("tags", []),
            },
        )
        
        result = await self.session.execute(stmt)
        await self.session.flush()
        
        # Get the document ID
        doc_result = await self.session.execute(
            select(Document.id).where(
                Document.repository_id == repository_id,
                Document.path == path,
                Document.git_ref == git_ref,
            )
        )
        return doc_result.scalar_one()
    
    async def save_chunk(
        self,
        document_id: UUID,
        chunk_index: int,
        content: str,
        token_count: int,
        metadata: dict[str, Any],
    ) -> UUID:
        """Save document chunk."""
        from sqlalchemy.dialects.postgresql import insert
        
        stmt = insert(DocumentChunk).values(
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            language=metadata.get("language", ""),
            area=metadata.get("area", Area.UNKNOWN.value),
            file_type=metadata.get("file_type", FileType.UNKNOWN.value),
            symbols_json=metadata.get("symbols", []),
            tags_json=metadata.get("tags", []),
        ).on_conflict_do_nothing(
            index_elements=["document_id", "chunk_index"],
        )
        
        await self.session.execute(stmt)
        await self.session.flush()
        
        # Get chunk ID
        chunk_result = await self.session.execute(
            select(DocumentChunk.id).where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.chunk_index == chunk_index,
            )
        )
        return chunk_result.scalar_one()
    
    async def save_chunk_embedding(
        self,
        chunk_id: UUID,
        embedding: list[float],
        model: str,
    ) -> None:
        """Save chunk embedding."""
        from sqlalchemy.dialects.postgresql import insert
        
        stmt = insert(ChunkEmbedding).values(
            chunk_id=chunk_id,
            embedding_model=model,
            embedding=embedding,
        ).on_conflict_do_update(
            index_elements=["chunk_id"],
            set_={
                "embedding_model": model,
                "embedding": embedding,
            },
        )
        
        await self.session.execute(stmt)
