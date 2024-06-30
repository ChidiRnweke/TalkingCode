import asyncio
from datetime import date
from backend.errors import MaximumSpendError
from backend.retrieval_augmented_generation.retrieve import (
    EmbeddedResponse,
    EmbeddingService,
    RetrievalAugmentedGeneration,
    RetrievedContext,
    SQLRetrievalService,
    GenerationService,
    PreviousQAs,
)
from backend.retrieval_augmented_generation import InputQuery

import numpy as np
import pytest
from logging import Logger

logger = Logger("backend_logger")


def answer_to_query(query: InputQuery) -> str:
    return f"Answer to {query.query}"


class StubGenerationService(GenerationService):
    async def augmented_generation(
        self, query: InputQuery, context: list[RetrievedContext]
    ) -> tuple[str, int]:
        answer = answer_to_query(query)
        spend = 1 if query.query == "spend" else 0
        return answer, spend

    def get_chat_model_name(self) -> str:
        return "chat_model"


class StubEmbeddingService(EmbeddingService):
    async def embed(self, text: str) -> EmbeddedResponse:
        tokens = 1 if text == "spend" else 0
        tokens = 10000000 if text == "high spend" else tokens
        return EmbeddedResponse(np.random.rand(3072).tolist(), tokens)

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
        obtained = await rag.retrieval_augmented_generation(input, 1)
        assert obtained.response == expected

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
        first = await rag.retrieval_augmented_generation(input, 1)
        second_query = InputQuery(
            query="test2", previous_context=previous, session_id=first.session_id
        )
        obtained = await rag.retrieval_augmented_generation(second_query, 1)

        expected = answer_to_query(second_query)
        assert obtained.response == expected

    async def test_retrieval_error_with_context_and_no_session_id(
        self, retrieval_service: SQLRetrievalService
    ):
        rag = RetrievalAugmentedGeneration(
            retrieval_service=retrieval_service,
            generation_service=StubGenerationService(),
            embedding_service=StubEmbeddingService(),
            max_spend=1,
            date=date.today(),
        )
        previous = [PreviousQAs(question="test", answer="answer")]
        with pytest.raises(Exception):
            input = InputQuery(query="test", previous_context=previous)
            await rag.retrieval_augmented_generation(input, 1)

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
        await rag.retrieval_augmented_generation(input, 1)
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
        spend_tasks = [rag.retrieval_augmented_generation(input, 1) for _ in range(10)]
        await asyncio.gather(*spend_tasks, return_exceptions=True)  # ignore exceptions
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
        await rag.retrieval_augmented_generation(input, 1)
        with pytest.raises(MaximumSpendError):
            await rag.retrieval_augmented_generation(input, 1)
