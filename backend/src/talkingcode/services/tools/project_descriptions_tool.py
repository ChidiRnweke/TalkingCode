"""Tool for discovering indexed project descriptions."""
from dataclasses import dataclass
from typing import Any

import structlog

from talkingcode.domain.models import RepositorySummary
from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.services.llm.openrouter_client import IOpenRouterClient

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True)
class ProjectDescriptionsTool:
    """Tool that returns summaries of indexed GitHub projects."""

    document_repository: DocumentRepository
    openrouter_client: IOpenRouterClient
    embedding_model: str
    embedding_dimensions: int

    name: str = "get_project_descriptions"
    timeout: int = 10

    @property
    def schema(self) -> dict[str, Any]:
        """Tool schema."""
        return {
            "description": (
                "Get descriptions and names of indexed GitHub projects. "
                "Optionally rank by relevance to a query using vector search in Postgres."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional relevance query. If provided, returns top-5 most relevant projects.",
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        }

    async def execute(self, query: str = "") -> dict[str, Any]:
        """Return project summaries, optionally ranked by query relevance."""
        summaries = await self._load_summaries(query)

        projects = [
            {
                "name": f"{s.owner}/{s.name}",
                "document_count": s.document_count,
                "languages": s.languages,
                "areas": s.areas,
                "last_ingested_at": s.last_ingested_at.isoformat() if s.last_ingested_at else None,
            }
            for s in summaries
        ]

        return {"projects": projects, "total": len(projects)}

    async def _load_summaries(self, query: str) -> list[RepositorySummary]:
        if not query.strip():
            return await self.document_repository.get_repository_summaries()

        embeddings = await self.openrouter_client.generate_embeddings(
            model=self.embedding_model,
            texts=[query],
            dimensions=self.embedding_dimensions,
        )
        if not embeddings:
            logger.warning("Project ranking embedding generation returned empty result")
            return await self.document_repository.get_repository_summaries()

        ranked = await self.document_repository.search_repository_summaries(
            query_embedding=embeddings[0],
            top_k=5,
        )
        if ranked:
            return ranked

        return await self.document_repository.get_repository_summaries()
