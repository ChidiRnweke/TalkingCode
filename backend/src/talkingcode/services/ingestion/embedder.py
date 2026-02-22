"""Embedding generator service."""

import asyncio
from dataclasses import dataclass
from typing import Protocol

import structlog

from talkingcode.errors import InfraError
from talkingcode.services.llm.openrouter_client import IOpenRouterClient

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

MAX_BATCH_SIZE = 100
MAX_RETRIES = 3


class IEmbedder(Protocol):
    """Protocol for embedding generation."""

    model: str

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        ...


@dataclass(slots=True)
class OpenRouterEmbedder:
    """Generates embeddings using OpenRouter embeddings API."""

    openrouter_client: IOpenRouterClient
    model: str = "openai/text-embedding-3-large"
    dimensions: int = 3072

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Splits into sub-batches of MAX_BATCH_SIZE and retries on failure.
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []

        for batch_start in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[batch_start : batch_start + MAX_BATCH_SIZE]
            embeddings = await self._embed_single_batch(batch)
            all_embeddings.extend(embeddings)

        logger.info("Generated embeddings", count=len(all_embeddings), model=self.model)
        return all_embeddings

    async def _embed_single_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a single batch with retry."""
        for attempt in range(MAX_RETRIES):
            try:
                return await self.openrouter_client.generate_embeddings(
                    model=self.model,
                    texts=texts,
                    dimensions=self.dimensions,
                )
            except Exception as exc:  # noqa: BLE001
                if attempt == MAX_RETRIES - 1:
                    raise InfraError(
                        f"OpenRouter embedding failed after {MAX_RETRIES} retries: {exc}"
                    ) from exc
                wait = 2**attempt
                logger.warning(
                    "Embedding request failed, retrying",
                    attempt=attempt,
                    error=str(exc),
                )
                await asyncio.sleep(wait)
                continue

        raise InfraError("OpenRouter embedding failed: max retries exceeded")
