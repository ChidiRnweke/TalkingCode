"""Retriever tool for semantic code search with conservative auto-filtering."""

from dataclasses import dataclass, field
from typing import Any, Protocol

import structlog
from talkingcode.repository.document_repository import IDocumentRepository
from talkingcode.services.ingestion.embedder import IOpenRouterEmbedder
from talkingcode.services.tools.query_intent import IQueryIntentExtractor

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


class IRetrieverTool(Protocol):
    """Protocol for retriever tool."""

    name: str
    schema: dict[str, Any]
    timeout: int

    async def execute(self, query: str) -> dict[str, Any]:
        """Execute retrieval with auto-detected metadata filters."""
        ...


@dataclass(slots=True)
class RetrieverTool:
    """Retrieve relevant code chunks with broad-first then refine behavior."""

    document_repository: IDocumentRepository
    embedder: IOpenRouterEmbedder
    intent_extractor: IQueryIntentExtractor
    openrouter_api_key: str
    intent_model: str = "deepseek/deepseek-v3.2"
    available_repos: list[str] = field(default_factory=list)

    name: str = "search_github"
    timeout: int = 15

    @property
    def schema(self) -> dict[str, Any]:
        """Tool schema."""
        return {
            "description": (
                "Semantic search across indexed GitHub repositories. "
                "Use focused natural-language queries; avoid large boolean OR chains. "
                "For vague questions, start broad, inspect results, then refine with follow-up searches."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "A concise natural-language search phrase. "
                            "Prefer one intent per call; avoid giant keyword bags like 'a OR b OR c ...'."
                        ),
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        }

    async def execute(self, query: str) -> dict[str, Any]:
        """Execute retrieval with auto-detected metadata filters."""
        logger.info("Searching GitHub index", query=query)

        intent = await self.intent_extractor.extract_query_intent(
            query=query,
            openrouter_api_key=self.openrouter_api_key,
            model=self.intent_model,
            available_repos=self.available_repos,
        )
        filters = self.intent_extractor.intent_to_filters(intent)
        search_query = intent.refined_query

        logger.info(
            "Intent extracted",
            refined_query=search_query,
            filters=None,
        )

        embeddings = await self.embedder.embed_batch([search_query])

        query_embedding = embeddings[0] if embeddings else []
        chunks = await self.document_repository.search_chunks(
            query_embedding=query_embedding,
            filters=filters if filters else None,
            top_k=8,
        )
        logger.info("Search completed", num_results=len(chunks))

        items = []
        for idx, chunk in enumerate(chunks, start=1):
            repo = chunk.metadata.get("repository", "")
            path = chunk.metadata.get("path", "")
            start_line = chunk.metadata.get("start_line")
            end_line = chunk.metadata.get("end_line")
            line_ref = f" (lines {start_line}-{end_line})" if start_line else ""

            items.append(
                {
                    "source_index": idx,
                    "repository": repo,
                    "path": path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "score": round(chunk.score, 4),
                    "content": f"[Source {idx}] {repo}: {path}{line_ref}\n{chunk.content[:700]}",
                }
            )
        return {
            "query": query,
            "refined_query": search_query,
            "filters_applied": filters,
            "items": items,
            "total": len(items),
        }
