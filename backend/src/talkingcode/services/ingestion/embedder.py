"""Embedding generation service."""

import asyncio
from dataclasses import dataclass
from typing import Protocol, cast

import structlog
from pydantic_ai import Embedder
from pydantic_ai.embeddings.openai import OpenAIEmbeddingModel
from pydantic_ai.embeddings.settings import EmbeddingSettings
from pydantic_ai.providers.openrouter import OpenRouterProvider
from talkingcode.errors import InfraError

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

MAX_RETRIES = 3


class IOpenRouterEmbedder(Protocol):
    """Protocol for embedding generators."""

    model: str

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""
        ...


@dataclass(slots=True)
class OpenRouterEmbedder:
    """Generates embeddings using Pydantic AI's OpenAI-compatible embedder."""

    api_key: str
    model: str
    dimensions: int | None

    def _embedder(self) -> Embedder:
        model_name = self.model.split(":", maxsplit=1)[-1]
        embedding_model = OpenAIEmbeddingModel(
            model_name,
            provider=OpenRouterProvider(
                api_key=self.api_key,
                app_url="https://talkingcode.dev",
                app_title="TalkingCode",
            ),
        )
        return Embedder(embedding_model)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts."""
        if not texts:
            return []

        settings = (
            cast(EmbeddingSettings, {"dimensions": self.dimensions})
            if self.dimensions
            else None
        )
        for attempt in range(MAX_RETRIES):
            try:
                result = await self._embedder().embed_documents(
                    texts,
                    settings=settings,
                )
                return [list(embedding) for embedding in result.embeddings]
            except Exception as exc:  # noqa: BLE001
                if attempt == MAX_RETRIES - 1:
                    raise InfraError(
                        f"OpenRouter embedding failed after {MAX_RETRIES} retries: {exc}"
                    ) from exc
                await asyncio.sleep(0.5 * (attempt + 1))

        raise InfraError("OpenRouter embedding failed: max retries exceeded")
