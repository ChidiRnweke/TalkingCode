from dataclasses import dataclass
from typing import Protocol

import aiohttp
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import ScoredPoint

from talkingcode.backend.errors import map_errors

from .generation import InputQuery
from .token_spend import TokenSpendStore


class RetrievalService(Protocol):
    """
    Interface for the retrieval service. Responsible for retrieving the top k
    contexts based on the embedded query. The query is embedded already by the
    `EmbeddingService`.

    """

    async def retrieve_top_k(
        self, embedded_query: "EmbeddedChunk"
    ) -> list["RetrievedContext"]:
        """

        Retrieves the top k contexts based on the embedded query.
        The contexts are the k most relevant documents to the embedded query.

        Args:
            embedded_query (EmbeddedResponse): The embedded query.
            k (int): The number of contexts to retrieve.

        Returns:
            (list[RetrievedContext]): The list of retrieved contexts.
        """
        ...


@dataclass(frozen=True, slots=True)
class RemainingSpend:
    """
    Class that represents the remaining spend based on the current spend and the maximum spend limit.
    This is the object that will later be deserialized to JSON and returned to the user.

    Args:
        remaining_spend (float): The remaining spend based on the current spend and the maximum spend limit.
    """

    remaining_spend: float


class EmbeddingService(Protocol):
    """
    The interface for the embedding service. Responsible for embedding the input query.
    The embedded query is then used to retrieve the top k contexts based on the
    embedded query by the `RetrievalService`.
    """

    embedding_model: str

    async def embed(self, input: InputQuery) -> "EmbeddedChunk":
        """
        Embeds the input text. Turns the input text into a list of floats that represent the text.
        The embedded response also contains the number of tokens spent on the embedding.

        Args:
            text (str): The text to embed.

        Returns:
            (EmbeddedResponse): The embedded response. Contains the embedding and the number of tokens spent.
        """
        ...


@dataclass(frozen=True, slots=True)
class RetrievedContext:
    """
    This is a domain class and is used to represent the context retrieved from the database. Its
    main purpose is to provide a structured representation of the context that is retrieved from the
    database. This simplifies testing, all of the logic relies on domain objects rather than database
    specific types.

    The class also provides helpers to enrich the file content with additional information such as
    the file name, repository name, path in the repository, and file extension. This is useful for
    generating the response to the user.

    Args:
        distance (float): The distance between the embedded query and the retrieved context.
        file_name (str): The name of the file.
        repository_name (str): The name of the repository.
        path_in_repo (str): The path of the file in the repository.
        extension (str): The file extension.
        url (str): The URL to the file content.
    """

    distance: float
    file_name: str
    repository_name: str
    path_in_repo: str
    extension: str
    url: str

    async def to_context(self) -> str:
        """Retrieves the file content from the URL and enriches it with additional information such as
        the file name, repository name, path in the repository, and file extension. This may
        improve generation quality by providing additional context to the model. The method is asynchronous
        because it fetches the file content from the URL. The data isn't persisted as such, it is fetched
        on-demand when needed.

        Returns:
            (str): The file content enriched with additional information.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                with map_errors():
                    file_content = await response.text()
        return self._enrich_file_content(file_content)

    def _enrich_file_content(self, file_content: str) -> str:
        """Enriches the file content with additional information such as the file name, repository name,
        path in the repository, and file extension. This may improve generation quality by providing
        additional context to the model.

        Args:
            file_content (str): The file content.

        Returns:
            (str): The file content enriched with additional information.
        """
        file_name = f"\nThe file name is {self.file_name}.\n"
        file_place_in_project = f"The file is located at {self.path_in_repo}.\n"
        file_extension = f"The file extension is {self.extension}.\n"
        return file_content + file_name + file_place_in_project + file_extension


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    """
    A class that represents the embedded response. This class is used to represent the response
    generated by the embedding service. The embedded response contains the embedding and the number
    of tokens spent on the embedding. This data class is used to pass the embedded response between
    the `EmbeddingService` and the `RetrievalService`.

    Args:
        embedding (list[float]): The embedded query.
        token_count (int): The number of tokens spent on the embedding.
    """

    embedding: list[float]


@dataclass(frozen=True)
class OpenAIEmbeddingService(EmbeddingService):
    """
    A class that performs text embedding using OpenAI's API. The class is responsible for embedding
    the input text. The embedded text is then used to retrieve the top k contexts based on the embedded
    query by the `RetrievalService`. The class is a wrapper around OpenAI's SDK and provides a more
    testable and maintainable interface. It implements the `EmbeddingService` interface.

    Args:
        client (AsyncOpenAI): The OpenAI client used for text embedding.
            Relies on the `OPENAI_EMBEDDING_API_KEY` environment variable.
        embedding_model (str): The name of the embedding model used for text embedding.
            In practice this is `text-embedding-3-large` but it is configurable through environment variables.
            It can directly be set with the `EMBEDDING_MODEL`.
    """

    client: AsyncOpenAI
    embedding_model: str
    token_store: TokenSpendStore

    async def embed(self, input: InputQuery) -> EmbeddedChunk:
        """
        Embeds the input text. Turns the input text into a list of floats that represent the text.
        The embedded response also contains the number of tokens spent on the embedding.

        Args:
            text (str): The text to embed.

        Returns:
            EmbeddedResponse: The embedded response. Contains the embedding and the number of tokens spent.
        """
        with map_errors():
            response = await self.client.embeddings.create(
                input=[input.query], model=self.embedding_model
            )
        await self.token_store.store_token_spent(
            session_id=input.session_id,
            token_count=response.usage.total_tokens,
            model_name=self.embedding_model,
        )
        return EmbeddedChunk(embedding=response.data[0].embedding)


@dataclass(frozen=True, slots=True)
class QdrantRetrievalService(RetrievalService):
    """
    A class that performs context retrieval using SQL. The class is responsible for retrieving the top k
    contexts based on the embedded query. The query is embedded already by the `EmbeddingService`. The class
    is a wrapper around SQLAlchemy and provides a more testable and maintainable interface. It implements
    the `RetrievalService` interface.

    Aside from this it is also responsible for storing the token spend and validating the session ID.

    Raises:
        (InputError): If a Session ID is provided, it must already exist.
    """

    client: AsyncQdrantClient
    top_k: int
    collection_name: str

    async def retrieve_top_k(
        self, embedded_query: EmbeddedChunk
    ) -> list[RetrievedContext]:
        """
        Retrieves the top k contexts based on the embedded query. The contexts are the k most relevant
        documents to the embedded query. The distance between the embedded query and the retrieved context
        is given by the cosine distance.

        In short, the lower the distance, the more similar the context is to the query.
        This is why we order by distance and limit the number of contexts to k.

        Args:
            embedded_query (EmbeddedResponse): The embedded query. This is done by the `EmbeddingService`.

        Returns:
            (list[RetrievedContext]): The list of retrieved contexts.
        """
        response = await self.client.search(
            collection_name=self.collection_name,
            query_vector=embedded_query.embedding,
            limit=self.top_k,
            with_payload=True,
        )

        return [self._point_to_context(hit) for hit in response]

    def _point_to_context(self, point: ScoredPoint) -> RetrievedContext:
        if not point.payload:
            raise ValueError("Payload is empty, cannot convert to context.")
        print(point.payload)
        return RetrievedContext(
            file_name=point.payload["file_name"],
            repository_name=point.payload["repository_name"],
            path_in_repo=point.payload["path_in_repo"],
            extension=point.payload["extension"],
            url=point.payload["url"],
            distance=point.score,
        )
