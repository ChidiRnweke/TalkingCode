from dataclasses import dataclass
from datetime import date
from typing import AsyncGenerator

from talkingcode.backend.errors import MaximumSpendError
from talkingcode.backend.rag.generation import GenerationService, InputQuery
from talkingcode.backend.rag.keyword_identifier import KeywordIdentifier
from talkingcode.backend.rag.retrieve import (
    EmbeddingService,
    RemainingSpend,
    RetrievalService,
    RetrievedContext,
)
from talkingcode.backend.rag.token_spend import TokenSpendStore


@dataclass(frozen=True)
class RetrievalAugmentedGeneration:
    """
    Class that performs retrieval-augmented generation given an input query and k value.

    Args:
        embedding_service: The embedding service used for text embedding.
        retrieval_service: The retrieval service used for context retrieval.
        generation_service: The generation service used for text generation.
        max_spend: The maximum spend limit for the retrieval-augmented generation.
        date (datetime.date): The date of the retrieval-augmented generation.
    """

    embedding_service: EmbeddingService
    retrieval_service: RetrievalService
    generation_service: GenerationService
    keyword_identification_service: KeywordIdentifier
    token_store: TokenSpendStore
    max_spend: float
    date: date

    async def rag_stream(self, input: InputQuery) -> AsyncGenerator[str, None]:
        """
        Performs retrieval-augmented generation given an input query and k value.
        The method enforces the spend limit, validates the session ID, retrieves the top k contexts,

        Args:
            input (InputQuery): The input query. Contains the user's question, and optionally,
                the previous context and session ID.
            k (int): The number of contexts to retrieve.


        Raises:
            (MaximumSpendError): If the current spend is greater than or equal to the maximum spend limit.
        """
        await self._enforce_spend_limit()
        retrieved = await self._retrieve_top_k(input)

        chunk_stream = self.generation_service.augmented_generation(input, retrieved)
        async for chunk in chunk_stream:
            yield chunk

    async def remaining_spend(self) -> "RemainingSpend":
        """

        Calculates the remaining spend based on the current spend and the maximum spend limit.
        The spend is capped at 0.

        Returns:
            (RemainingSpend): The remaining spend.
        """
        current_spend = await self.token_store.get_current_spend(self.date)
        remaining = round(self.max_spend - current_spend, 2)
        remaining = max(remaining, 0)
        return RemainingSpend(remaining)

    async def _enforce_spend_limit(self) -> None:
        """

        Enforces the spend limit by checking the current spend against the maximum spend limit.
        If the current spend is greater than or equal to the maximum spend limit, raises a `MaximumSpendError`.

        Raises:
            (MaximumSpendError): If the current spend is greater than or equal to the maximum spend limit.

        """
        current_spend = await self.token_store.get_current_spend(self.date)
        if current_spend >= self.max_spend:
            raise MaximumSpendError()

    async def _retrieve_top_k(self, input: InputQuery) -> list[RetrievedContext]:
        """
            embeds the input query and retrieves the top k contexts based on the embedded query.


        Returns:
            (tuple[list[RetrievedContext], int]): A tuple containing the list of retrieved contexts
                and the number of tokens spent. see `RetrievedContext` for more information.
        """
        result = await self.embedding_service.embed(input)
        keywords = await self.keyword_identification_service.identify_keywords(
            input.query
        )
        return await self.retrieval_service.retrieve_top_k(result, keywords)
