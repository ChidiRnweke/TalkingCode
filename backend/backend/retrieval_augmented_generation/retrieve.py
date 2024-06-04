from shared.database import EmbeddedDocumentModel
from openai import AsyncOpenAI
from dataclasses import dataclass
from typing import Protocol
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


@dataclass(frozen=True)
class EmbeddingResponse:
    embedding: list[float]
    token_count: int


class RetrievalService(Protocol):
    async def retrieve_top_k(
        self, embedded_query: EmbeddingResponse, k: int
    ) -> list[EmbeddedDocumentModel]: ...

    async def store_token_spent(self, token_count: int): ...


@dataclass(frozen=True)
class RetrievedContext:
    distance: float
    file_name: str
    repository_name: str
    path_in_repo: str
    extension: str

    @classmethod
    def from_document(
        cls, score: float, document: EmbeddedDocumentModel
    ) -> "RetrievedContext":
        return cls(
            distance=score,
            file_name=document.document.name,
            repository_name=document.document.repository_name,
            path_in_repo=document.document.path_in_repo,
            extension=document.document.file_extension,
        )


@dataclass(frozen=True)
class OpenAIService:
    client: AsyncOpenAI
    embedding_model: str
    chat_model: str

    async def embed(self, text: str) -> EmbeddingResponse:
        response = await self.client.embeddings.create(
            input=[text], model=self.embedding_model
        )
        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            token_count=response.usage.total_tokens,
        )

    async def augmented_generation(
        self, query: str, context: list[RetrievedContext]
    ) -> str: ...


@dataclass(frozen=True)
class SQLRetrievalService:
    async_session: AsyncSession

    async def retrieve_top_k(
        self, embedded_query: EmbeddingResponse, k: int
    ) -> list[RetrievedContext]:
        stmt = (
            select(EmbeddedDocumentModel)
            .order_by(
                EmbeddedDocumentModel.embedding.l2_distance(embedded_query.embedding)
            )
            .limit(k)
        )

        async with self.async_session.begin():
            result = await self.async_session.scalars(stmt)
            return [doc for doc in result]  # TODO: add distance to the return value

    async def store_token_spent(self, token_count: int):
        async with self.async_session.begin():
            ...  # TODO: Store token count in database. Make new table for this.


class EmbeddingService(Protocol):
    async def embed(self, text: str) -> EmbeddingResponse: ...

    async def augmented_generation(
        self, query: str, context: list[RetrievedContext]
    ) -> str: ...


async def retrieve_top_k(
    embedding_service: EmbeddingService,
    retrieval_service: RetrievalService,
    query: str,
    k: int,
) -> list[EmbeddedDocumentModel]:
    result = await embedding_service.embed(query)
    await retrieval_service.store_token_spent(result.token_count)
    return await retrieval_service.retrieve_top_k(result, k)
