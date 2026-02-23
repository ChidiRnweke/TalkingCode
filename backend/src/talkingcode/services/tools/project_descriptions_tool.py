"""Tool for discovering indexed project descriptions."""
from dataclasses import dataclass
from typing import Any

import structlog

from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.services.llm.openrouter_client import IOpenRouterClient

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True)
class ProjectDescriptionsTool:
    """Tool that returns summaries of all indexed GitHub projects."""

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
                "Get descriptions and names of all indexed GitHub projects. "
                "Optionally filter by relevance to a query using semantic similarity."
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
        """Return indexed project summaries, optionally ranked by query relevance."""
        summaries = await self.document_repository.get_repository_summaries()

        if not summaries:
            return {"projects": [], "total": 0}

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

        if query.strip():
            # Rank by cosine similarity between query embedding and project description embedding
            descriptions = [
                f"{p['name']}: {p['document_count']} files, languages: {', '.join(p['languages'])}, areas: {', '.join(p['areas'])}"
                for p in projects
            ]
            all_texts = [query] + descriptions

            embeddings = await self.openrouter_client.generate_embeddings(
                model=self.embedding_model,
                texts=all_texts,
                dimensions=self.embedding_dimensions,
            )

            if len(embeddings) == len(all_texts):
                query_emb = embeddings[0]
                from talkingcode.repository.document_repository import DocumentRepository

                scored = []
                for i, proj in enumerate(projects):
                    score = DocumentRepository._cosine_similarity(query_emb, embeddings[i + 1])
                    scored.append((score, proj))

                scored.sort(key=lambda x: x[0], reverse=True)
                projects = [p for _, p in scored[:5]]

        return {"projects": projects, "total": len(projects)}
