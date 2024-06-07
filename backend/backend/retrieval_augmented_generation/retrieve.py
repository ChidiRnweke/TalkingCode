import asyncio
from shared.database import EmbeddedDocumentModel, GithubFileModel, TokenSpendModel
from openai import AsyncOpenAI
from dataclasses import dataclass
from typing import Optional, Protocol, Self
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, model_validator
import aiohttp
import uuid
from backend.errors import InputError


@dataclass(frozen=True)
class RetrievalAugmentedGeneration:
    embedding_service: "EmbeddingService"
    retrieval_service: "RetrievalService"
    generation_service: "GenerationService"

    async def retrieval_augmented_generation(
        self, input: "InputQuery", k: int
    ) -> "RAGResponse":
        if input.session_id:
            await self.retrieval_service.validate_session_id(input.session_id)
            session_id = input.session_id
        else:
            session_id = str(uuid.uuid4())

        retrieved, tokens_spent = await self._retrieve_top_k(input, k)
        store_task = self.retrieval_service.store_token_spent(
            session_id,
            tokens_spent,
            self.embedding_service.get_embed_model_name(),
        )
        generation_task = self.generation_service.augmented_generation(input, retrieved)
        _, response = await asyncio.gather(store_task, generation_task)

        return RAGResponse(response=response, session_id=session_id)

    async def _retrieve_top_k(
        self, input: "InputQuery", k: int
    ) -> tuple[list["RetrievedContext"], int]:
        result = await self.embedding_service.embed(input.query)
        tokens_spent = result.token_count
        return (await self.retrieval_service.retrieve_top_k(result, k), tokens_spent)


class RAG(Protocol):

    async def retrieval_augmented_generation(
        self, input: "InputQuery", k: int
    ) -> "RAGResponse": ...


class RetrievalService(Protocol):
    async def retrieve_top_k(
        self, embedded_query: "EmbeddedResponse", k: int
    ) -> list["RetrievedContext"]: ...

    async def store_token_spent(
        self, session_id: str, token_count: int, model_name: str
    ): ...

    async def validate_session_id(self, session_id: str) -> None: ...


class GenerationService(Protocol):
    async def augmented_generation(
        self, query: "InputQuery", context: list["RetrievedContext"]
    ) -> str: ...


class EmbeddingService(Protocol):

    async def embed(self, text: str) -> "EmbeddedResponse": ...

    def get_embed_model_name(self) -> str: ...


class PreviousQAs(BaseModel):
    question: str
    answer: str


class InputQuery(BaseModel):
    query: str
    previous_context: Optional[list[PreviousQAs]] = None
    session_id: Optional[str] = None

    def previous_context_to_dict(self) -> list[dict[str, str]]:
        res = []
        if self.previous_context:
            for qa in self.previous_context:
                res.append({"role": "user", "content": qa.question})
                res.append({"role": "assistant", "content": qa.answer})
        return res

    @model_validator(mode="after")
    def validate_previous_context(self) -> Self:
        if self.session_id and not self.previous_context:
            raise ValueError(
                "Previous context must be provided if session_id is present."
            )
        elif not self.session_id and self.previous_context:
            raise ValueError(
                "Session ID must be provided if previous context is present."
            )
        return self


@dataclass(frozen=True)
class RAGResponse:
    response: str
    session_id: str


@dataclass(frozen=True)
class RetrievedContext:
    distance: float
    file_name: str
    repository_name: str
    path_in_repo: str
    extension: str
    url: str

    @classmethod
    def from_document(
        cls, score: float, document: GithubFileModel
    ) -> "RetrievedContext":
        return cls(
            distance=score,
            file_name=document.name,
            repository_name=document.repository_name,
            path_in_repo=document.path_in_repo,
            extension=document.file_extension,
            url=document.content_url,
        )

    async def to_context(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                file_content = await response.text()
        return self._enrich_file_content(file_content)

    def _enrich_file_content(self, file_content: str) -> str:
        file_name = f"\nThe file name is {self.file_name}.\n"
        file_place_in_project = f"The file is located at {self.path_in_repo}.\n"
        file_extension = f"The file extension is {self.extension}.\n"
        return file_content + file_name + file_place_in_project + file_extension


@dataclass(frozen=True)
class EmbeddedResponse:
    embedding: list[float]
    token_count: int


@dataclass(frozen=True)
class OpenAIEmbeddingService:
    client: AsyncOpenAI
    embedding_model: str

    async def embed(self, text: str) -> EmbeddedResponse:
        response = await self.client.embeddings.create(
            input=[text], model=self.embedding_model
        )
        return EmbeddedResponse(
            embedding=response.data[0].embedding,
            token_count=response.usage.total_tokens,
        )

    def get_embed_model_name(self) -> str:
        return self.embedding_model


@dataclass(frozen=True)
class OpenAIGenerationService:
    client: AsyncOpenAI
    chat_model: str
    system_prompt: str

    async def augmented_generation(
        self, query: InputQuery, context: list[RetrievedContext]
    ) -> str:
        ctx = await asyncio.gather(*[c.to_context() for c in context])
        model_input = self._create_model_input(query, ctx)
        response = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=model_input,  # type: ignore
        )
        response = response.choices[0].message.content or ""
        return self.__add_sources(response, context)

    def _create_model_input(
        self, input: InputQuery, ctx: list[str]
    ) -> list[dict[str, str]]:
        query_with_ctx = f"""The user's question is {input.query}.
        You have access to additional context in a list of code files: {ctx}"""

        previous_qas = input.previous_context_to_dict()

        model_input = [{"role": "system", "content": self.system_prompt}]
        model_input.extend(previous_qas)
        model_input.append({"role": "user", "content": query_with_ctx})
        return model_input

    def __add_sources(self, answer: str, retrieved: list[RetrievedContext]) -> str:
        sources = [
            f"* {r.file_name} in {r.repository_name}, {r.url} path is: \n"
            for r in retrieved
        ]
        return f"{answer}\n To answer this question, I used the following sources: \n {''.join(sources)}"


@dataclass(frozen=True)
class SQLRetrievalService:
    async_session: AsyncSession

    async def retrieve_top_k(
        self, embedded_query: EmbeddedResponse, k: int
    ) -> list[RetrievedContext]:

        stmt = (
            select(
                EmbeddedDocumentModel.embedding.cosine_distance(
                    embedded_query.embedding
                ).label("distance"),
                EmbeddedDocumentModel,
            )
            .join(
                GithubFileModel, EmbeddedDocumentModel.document_id == GithubFileModel.id
            )
            .order_by("distance")
            .limit(k)
        )

        async with self.async_session.begin():
            result = await self.async_session.execute(stmt)
            documents = result.all()

        return [
            RetrievedContext.from_document(doc[0], doc[1].document) for doc in documents
        ]

    async def store_token_spent(
        self, session_id: str, token_count: int, model_name: str
    ) -> None:
        async with self.async_session.begin():
            token_spend = TokenSpendModel(
                session_id=session_id,
                token_count=token_count,
                model=model_name,
            )
            self.async_session.add(token_spend)

    async def validate_session_id(self, session_id: str) -> None:
        stmt = select(TokenSpendModel).where(TokenSpendModel.session_id == session_id)
        async with self.async_session.begin():
            result = await self.async_session.execute(stmt)
            if not result.scalar():
                raise InputError("If a Session ID is provided, it must already exist.")
