"""Retriever tool for semantic search with auto-detected metadata filtering."""
from dataclasses import dataclass, field
from typing import Any

import structlog

from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.services.llm.openrouter_client import IOpenRouterClient
from talkingcode.services.tools.query_intent import (
    extract_query_intent,
    intent_to_filters,
)

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True)
class RetrieverTool:
    """Tool for retrieving relevant code chunks with auto metadata filtering."""

    document_repository: DocumentRepository
    openrouter_client: IOpenRouterClient
    embedding_model: str
    embedding_dimensions: int
    intent_model: str = "deepseek/deepseek-v3.2"
    available_repos: list[str] = field(default_factory=list)

    name: str = "search_github"
    timeout: int = 15

    @property
    def schema(self) -> dict[str, Any]:
        """Tool schema."""
        return {
            "description": "Vector search across Chidi's indexed GitHub code",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        }

    async def execute(self, query: str) -> dict[str, Any]:
        """Execute retrieval with auto-detected metadata filters."""
        logger.info("Searching GitHub index", query=query)

        # Extract intent and build filters
        intent = await extract_query_intent(
            query=query,
            openrouter_client=self.openrouter_client,
            model=self.intent_model,
            available_repos=self.available_repos,
        )
        filters = intent_to_filters(intent)
        search_query = intent.refined_query

        logger.info(
            "Intent extracted",
            refined_query=search_query,
            filters=filters,
        )

        embeddings = await self.openrouter_client.generate_embeddings(
            model=self.embedding_model,
            texts=[search_query],
            dimensions=self.embedding_dimensions,
        )

        query_embedding = embeddings[0] if embeddings else []
        chunks = await self.document_repository.search_chunks(
            query_embedding=query_embedding,
            filters=filters if filters else None,
            top_k=8,
        )

        items = []
        for idx, chunk in enumerate(chunks, start=1):
            repo = chunk.metadata.get("repository", "")
            path = chunk.metadata.get("path", "")
            start_line = chunk.metadata.get("start_line")
            end_line = chunk.metadata.get("end_line")
            line_ref = f" (lines {start_line}-{end_line})" if start_line else ""

            items.append({
                "source_index": idx,
                "repository": repo,
                "path": path,
                "start_line": start_line,
                "end_line": end_line,
                "score": round(chunk.score, 4),
                "content": f"[Source {idx}] {repo}: {path}{line_ref}\n{chunk.content[:700]}",
            })

        return {
            "query": query,
            "refined_query": search_query,
            "filters_applied": filters,
            "items": items,
            "total": len(items),
        }
