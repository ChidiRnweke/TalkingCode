from datetime import date
from backend.retrieval_augmented_generation.retrieve import (
    PreviousQAs,
    RetrievalAugmentedGeneration,
    EmbeddingService,
    GenerationService,
    RetrievalService,
    EmbeddedResponse,
    RetrievedContext,
    InputQuery,
)
from backend.errors import MaximumSpendError, InputError
from dataclasses import dataclass
import pytest


@dataclass
class StubRetrievalService(RetrievalService):

    async def retrieve_top_k(self, query: str, top_k: int) -> list[str]:
        return ["response {k}" for k in range(top_k)]

    async def store_token_spent(
        self, session_id: str, token_count: int, model_name: str
    ) -> None:
        return

    async def validate_session_id(self, session_id: str) -> None:
        if session_id == "invalid":
            raise InputError("Invalid session ID")

    async def get_current_spend(self, date: date) -> float:
        if date == date.today():
            return 0.0
        else:
            return 1000


@dataclass
class StubGenerationService(GenerationService):
    async def augmented_generation(
        self, query: InputQuery, context: list[RetrievedContext]
    ) -> tuple[str, int]:
        return query.query + " response", 0

    def get_chat_model_name(self) -> str:
        return "stub-chat-model"


@dataclass
class StubEmbeddingService(EmbeddingService):
    async def embed(self, text: str) -> EmbeddedResponse:
        embeddings = [1.0, 2.0, 3.0]
        token_count = len(text)
        return EmbeddedResponse(embeddings, token_count)

    def get_embed_model_name(self) -> str:
        return "stub-embedding-model"


@pytest.fixture
def rag_service(request: pytest.FixtureRequest):
    return RetrievalAugmentedGeneration(
        StubEmbeddingService(),
        StubRetrievalService(),
        StubGenerationService(),
        1,
        request.param,
    )


class TestInputQuery:

    def test_input_query_can_have_empty_session_id(self):
        query = InputQuery(query="query")
        assert query.session_id is None

    def test_input_query_can_have_empty_previous_context(self):
        query = InputQuery(query="query")
        assert query.previous_context is None

    def test_input_query_can_not_have_previous_context_without_session_id(self):
        prev_qas = [PreviousQAs(question="q", answer="a")]
        with pytest.raises(ValueError):
            InputQuery(query="query", previous_context=prev_qas)

    def test_input_query_can_not_have_session_id_without_previous_context(self):
        with pytest.raises(ValueError):
            InputQuery(query="query", session_id="session")

    def test_input_query_can_have_previous_context_with_session_id(self):
        prev_qas = [PreviousQAs(question="q", answer="a")]
        query = InputQuery(
            query="query", previous_context=prev_qas, session_id="session"
        )
        assert query.previous_context == prev_qas


class TestRAGService:

    @pytest.mark.asyncio
    @pytest.mark.parametrize("rag_service", [date.today()], indirect=True)
    async def test_retrieval_augmented_generation(
        self, rag_service: RetrievalAugmentedGeneration
    ):
        query = InputQuery(query="query")
        response = await rag_service.retrieval_augmented_generation(query, 1)
        assert response.response == "query response"

    @pytest.mark.parametrize("rag_service", [date.today()], indirect=True)
    @pytest.mark.asyncio
    async def test_receiving_session_id(
        self, rag_service: RetrievalAugmentedGeneration
    ):
        query = InputQuery(query="query")
        response = await rag_service.retrieval_augmented_generation(query, 1)
        assert response.session_id is not None

    @pytest.mark.asyncio
    @pytest.mark.parametrize("rag_service", [date.today()], indirect=True)
    async def test_invalid_session_id_is_an_error(
        self, rag_service: RetrievalAugmentedGeneration
    ):
        prev_qas = [PreviousQAs(question="q", answer="a")]
        query = InputQuery(
            query="query", previous_context=prev_qas, session_id="invalid"
        )
        with pytest.raises(InputError):
            await rag_service.retrieval_augmented_generation(query, 1)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "rag_service", [date.min], indirect=True
    )  # Any date other than today
    async def test_throw_error_on_max_spend_exceeded(
        self, rag_service: RetrievalAugmentedGeneration
    ):
        query = InputQuery(query="query")
        with pytest.raises(MaximumSpendError):
            await rag_service.retrieval_augmented_generation(query, 1)
