"""Document repository."""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.domain.models import RetrievedChunk, RepositorySummary
from talkingcode.enums import Area, FileType
from talkingcode.models.orm import ChunkEmbedding, Document, DocumentChunk, Repository


@dataclass(slots=True)
class DocumentRepository:
    """Repository for document operations."""

    session: AsyncSession
    _embedding_dimensions: int = 3072

    async def search_chunks(
        self,
        query_embedding: list[float],
        filters: dict[str, Any] | None = None,
        top_k: int = 10,
    ) -> list[RetrievedChunk]:
        """Search chunks by cosine similarity with optional metadata filtering."""
        if len(query_embedding) != self._embedding_dimensions:
            return []

        distance = ChunkEmbedding.embedding.cosine_distance(query_embedding)
        similarity = (1 - distance).label("similarity")
        stmt = (
            select(DocumentChunk, Document, Repository, similarity)
            .join(ChunkEmbedding, ChunkEmbedding.chunk_id == DocumentChunk.id)
            .join(Document, Document.id == DocumentChunk.document_id)
            .join(Repository, Repository.id == Document.repository_id)
            .order_by(distance)
            .limit(top_k)
        )

        if filters:
            if filters.get("repository_name"):
                repo_name = filters["repository_name"]
                if "/" in repo_name:
                    owner, name = repo_name.split("/", 1)
                    stmt = stmt.where(Repository.owner == owner, Repository.name == name)
                else:
                    stmt = stmt.where(Repository.name == repo_name)

            if filters.get("language"):
                stmt = stmt.where(DocumentChunk.language == filters["language"])

            if filters.get("area"):
                stmt = stmt.where(DocumentChunk.area == filters["area"])

            if filters.get("file_type"):
                stmt = stmt.where(DocumentChunk.file_type == filters["file_type"])

            symbols = filters.get("symbols")
            if isinstance(symbols, list) and symbols:
                stmt = stmt.where(DocumentChunk.symbols_json.op("?|")(array(symbols)))

            tags = filters.get("tags")
            if isinstance(tags, list) and tags:
                stmt = stmt.where(DocumentChunk.tags_json.op("?|")(array(tags)))

        result = await self.session.execute(stmt)

        candidates: list[RetrievedChunk] = []
        for chunk, document, repo, score in result.all():
            repo_str = f"{repo.owner}/{repo.name}" if repo else ""
            candidates.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    document_id=document.id,
                    content=chunk.content,
                    score=float(score),
                    metadata={
                        "path": document.path,
                        "git_ref": document.git_ref,
                        "language": chunk.language,
                        "area": chunk.area,
                        "file_type": chunk.file_type,
                        "repository": repo_str,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                    },
                )
            )

        return candidates
    
    async def get_file_chunks(
        self,
        repository_id: UUID,
        path: str,
    ) -> list[dict[str, Any]] | None:
        """Retrieve all chunks for a file, ordered by chunk_index."""
        result = await self.session.execute(
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(
                Document.repository_id == repository_id,
                Document.path == path,
            )
            .order_by(DocumentChunk.chunk_index)
        )
        rows = result.all()
        if not rows:
            return None
        return [
            {
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "language": chunk.language,
                "area": chunk.area,
                "file_type": chunk.file_type,
                "symbols": chunk.symbols_json or [],
            }
            for chunk, _doc in rows
        ]

    async def get_repository_summaries(self) -> list[RepositorySummary]:
        """Get summary info for all repositories with indexed content."""
        result = await self.session.execute(
            select(
                Repository.id,
                Repository.owner,
                Repository.name,
                Repository.last_ingested_at,
                func.count(Document.id).label("document_count"),
            )
            .outerjoin(Document, Document.repository_id == Repository.id)
            .group_by(Repository.id)
            .order_by(Repository.created_at.desc())
        )
        summaries = []
        for row in result.all():
            # Get distinct languages and areas for this repo
            lang_result = await self.session.execute(
                select(func.distinct(DocumentChunk.language))
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(
                    Document.repository_id == row.id,
                    DocumentChunk.language != "",
                )
            )
            languages = [r[0] for r in lang_result.all()]

            area_result = await self.session.execute(
                select(func.distinct(DocumentChunk.area))
                .join(Document, Document.id == DocumentChunk.document_id)
                .where(
                    Document.repository_id == row.id,
                    DocumentChunk.area != Area.UNKNOWN.value,
                )
            )
            areas = [r[0] for r in area_result.all()]

            summaries.append(
                RepositorySummary(
                    repository_id=row.id,
                    owner=row.owner,
                    name=row.name,
                    document_count=row.document_count,
                    languages=languages,
                    areas=areas,
                    last_ingested_at=row.last_ingested_at,
                )
            )
        return summaries

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
        
        await self.session.execute(stmt)
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
