from datetime import date, datetime
from backend.errors import InputError
from backend.retrieval_augmented_generation.retrieve import (
    SQLRetrievalService,
    EmbeddedResponse,
)
import numpy as np
import pytest
from shared.database import (
    TokenSpendModel,
)
from logging import Logger

logger = Logger("backend_logger")


@pytest.mark.asyncio(scope="session")
class TestInfrastructure:

    async def test_storing_tokens(self, retrieval_service: SQLRetrievalService):
        await retrieval_service.store_token_spent("session_id", 100, "embedding_model")

    async def test_retrieving_context(self, retrieval_service: SQLRetrievalService):
        query = EmbeddedResponse(np.random.rand(3072).tolist(), 100)
        obtained = await retrieval_service.retrieve_top_k(query, 1)
        assert len(obtained) == 1

    async def test_retrieving_context_with_k_greater_than_available(
        self, retrieval_service: SQLRetrievalService
    ):
        query = EmbeddedResponse(np.random.rand(3072).tolist(), 100)
        obtained = await retrieval_service.retrieve_top_k(query, 1000)
        assert len(obtained) == 2

    async def test_original_context_is_returned(
        self, retrieval_service: SQLRetrievalService
    ):
        query = EmbeddedResponse(np.random.rand(3072).tolist(), 100)
        obtained = await retrieval_service.retrieve_top_k(query, 100)
        file_names = {file.file_name for file in obtained}
        assert {"file1", "file2"} == file_names

    async def test_retrieving_tokens(self, retrieval_service: SQLRetrievalService):
        input = 100
        expected = 100 * 0.00001
        token_spend = TokenSpendModel(
            session_id="session_id",
            token_count=input,
            model="embedding_model",
            timestamp=datetime.max,
        )
        retrieval_service.async_session.add(token_spend)
        await retrieval_service.async_session.commit()

        obtained = await retrieval_service.get_current_spend(date.max)
        assert obtained == expected

    async def test_session_id_not_found_raises_error(
        self, retrieval_service: SQLRetrievalService
    ):
        with pytest.raises(InputError):
            await retrieval_service.validate_session_id("not in")

    async def test_validating_session_id(self, retrieval_service: SQLRetrievalService):
        expected = "valid_session_id"
        await retrieval_service.store_token_spent(expected, 100, "embedding_model")
        await retrieval_service.validate_session_id(expected)
        assert True

    async def test_no_tokens_spent_is_0_spend(
        self, retrieval_service: SQLRetrievalService
    ):
        expected = 0
        obtained = await retrieval_service.get_current_spend(date.min)
        assert obtained == expected
