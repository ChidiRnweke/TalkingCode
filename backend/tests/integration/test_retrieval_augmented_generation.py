from datetime import date
from typing import AsyncGenerator
from backend.errors import MaximumSpendError
from backend.rag.retrieve import (
    EmbeddedChunk,
    EmbeddingService,
    RetrievedContext,
    SQLRetrievalService,
)

from backend.rag.generation import GenerationService, PreviousQAs
from backend.rag import InputQuery, RetrievalAugmentedGeneration

import numpy as np
import pytest
from logging import Logger

logger = Logger("app_logger")


def answer_to_query(query: InputQuery) -> str:
    return f"Answer to {query.query}"


class StubGenerationService(GenerationService):
    async def augmented_generation(
        self, query: "InputQuery", context: list["RetrievedContext"]
    ) -> AsyncGenerator[tuple[str, int | None], None]:
        answer = answer_to_query(query)
        spend = 1 if query.query == "spend" else 0
        yield answer, spend

    def get_chat_model_name(self) -> str:
        return "chat_model"


class StubEmbeddingService(EmbeddingService):
    async def embed(self, text: str) -> EmbeddedChunk:
        tokens = 1 if text == "spend" else 0
        tokens = 10000000 if text == "high spend" else tokens
        return EmbeddedChunk(np.random.rand(3072).tolist(), tokens)

    def get_embed_model_name(self) -> str:
        return "embedding_model"


@pytest.mark.asyncio(scope="session")
class TestRetrievalAugmentedGeneration:
    async def test_retrieval_no_context(self, retrieval_service: SQLRetrievalService):
        rag = RetrievalAugmentedGeneration(
            retrieval_service=retrieval_service,
            generation_service=StubGenerationService(),
            embedding_service=StubEmbeddingService(),
            max_spend=2,
            date=date.today(),
        )
        input = InputQuery(query="test")
        expected = answer_to_query(input)
        response = ""
        async for chunk in rag.retrieval_augmented_generation(input, 1, "test"):
            response += chunk
        assert response == expected

    async def test_retrieval_with_context(self, retrieval_service: SQLRetrievalService):
        rag = RetrievalAugmentedGeneration(
            retrieval_service=retrieval_service,
            generation_service=StubGenerationService(),
            embedding_service=StubEmbeddingService(),
            max_spend=2,
            date=date.today(),
        )
        previous = [PreviousQAs(question="test", answer="answer")]
        input = InputQuery(query="test")
        id = "test"
        resp1 = ""
        async for chunk in rag.retrieval_augmented_generation(input, 1, id):
            resp1 += chunk

        second_query = InputQuery(
            query="test2", previous_context=previous, session_id=id
        )
        obtained = ""
        async for chunk in rag.retrieval_augmented_generation(second_query, 1, id):
            obtained += chunk

        expected = answer_to_query(second_query)
        assert obtained == expected

    async def test_retrieval_spend_limit(self, retrieval_service: SQLRetrievalService):
        max_spend = 2 * 0.00001  # 2 tokens
        expected = 0
        rag = RetrievalAugmentedGeneration(
            retrieval_service=retrieval_service,
            generation_service=StubGenerationService(),
            embedding_service=StubEmbeddingService(),
            max_spend=max_spend,
            date=date.today(),
        )

        input = InputQuery(query="spend")
        id = "spend"
        async for chunk in rag.retrieval_augmented_generation(input, 1, id):
            pass
        obtained = await rag.remaining_spend()
        assert obtained.remaining_spend == expected

    async def test_spend_limit_zero_if_exceeded(
        self, retrieval_service: SQLRetrievalService
    ):
        max_spend = 2 * 0.00001
        expected = 0
        rag = RetrievalAugmentedGeneration(
            retrieval_service=retrieval_service,
            generation_service=StubGenerationService(),
            embedding_service=StubEmbeddingService(),
            max_spend=max_spend,
            date=date.today(),
        )
        input = InputQuery(query="spend")
        for i in range(10):
            id = "spend"
            async for _ in rag.retrieval_augmented_generation(input, 1, id):
                pass
        obtained = await rag.remaining_spend()
        assert obtained.remaining_spend == expected

    async def test_spend_error_thrown_if_limit_exceeded(
        self, retrieval_service: SQLRetrievalService
    ):
        max_spend = 50 * 0.00001
        rag = RetrievalAugmentedGeneration(
            retrieval_service=retrieval_service,
            generation_service=StubGenerationService(),
            embedding_service=StubEmbeddingService(),
            max_spend=max_spend,
            date=date.today(),
        )
        input = InputQuery(query="high spend")
        async for _ in rag.retrieval_augmented_generation(input, 1, "high spend"):
            pass
        with pytest.raises(MaximumSpendError):
            async for _ in rag.retrieval_augmented_generation(input, 1, "high spend"):
                pass
