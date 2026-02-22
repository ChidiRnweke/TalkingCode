"""Embedding generator service."""

import asyncio
from dataclasses import dataclass
from typing import Protocol

import httpx
import structlog

from talkingcode.errors import InfraError

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
MAX_BATCH_SIZE = 100
MAX_RETRIES = 3


class IEmbedder(Protocol):
    """Protocol for embedding generation."""

    model: str

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""


@dataclass(slots=True)
class OpenAIEmbedder:
    """Generates embeddings using OpenAI's API."""

    openai_api_key: str
    model: str = "text-embedding-3-small"
    dimensions: int = 1536

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
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        OPENAI_EMBEDDINGS_URL,
                        headers={
                            "Authorization": f"Bearer {self.openai_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "input": texts,
                            "dimensions": self.dimensions,
                        },
                        timeout=60.0,
                    )

                    if response.status_code in (429, 503):
                        wait = 2**attempt
                        logger.warning(
                            "Rate limited, retrying",
                            attempt=attempt,
                            wait_seconds=wait,
                        )
                        await asyncio.sleep(wait)
                        continue

                    response.raise_for_status()
                    data = response.json()

                    sorted_data = sorted(data["data"], key=lambda x: x["index"])
                    return [item["embedding"] for item in sorted_data]

            except httpx.HTTPStatusError as exc:
                if attempt == MAX_RETRIES - 1:
                    raise InfraError(
                        f"OpenAI embedding failed after {MAX_RETRIES} retries: {exc}"
                    ) from exc
                wait = 2**attempt
                logger.warning(
                    "Embedding request failed, retrying",
                    attempt=attempt,
                    error=str(exc),
                )
                await asyncio.sleep(wait)

        raise InfraError("OpenAI embedding failed: max retries exceeded")
