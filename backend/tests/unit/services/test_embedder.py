import pytest

from talkingcode.services.ingestion.embedder import OpenRouterEmbedder


@pytest.mark.asyncio
async def test_embedder_empty_batch_returns_empty():
    embedder = OpenRouterEmbedder(
        api_key="test-key", model="m", dimensions=128
    )
    result = await embedder.embed_batch([])
    assert result == []
