import asyncio
import logging
from openai import AsyncOpenAI
from typing import Any, Coroutine
from talkingcode.pipelines.processing.models import AuthHeader, FileMetadata, GitHubFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from talkingcode.shared.database import EmbeddedDocumentModel, GithubFileModel
from dataclasses import dataclass
import aiohttp
import tiktoken
from tiktoken import Encoding
from openai.types import CreateEmbeddingResponse
from typing import Protocol


app_logger = logging.getLogger("app_logger")


@dataclass(frozen=True, slots=True)
class EmbeddingWithCount:
    """
    This class is used to store the embeddings of a file as well as the total number of tokens in the file.
    We store the total number of tokens in the file so that we can calculate the cost of the embedding.

    Args:
        embedding (list[float]): The embeddings of the file.
        total_tokens (int): The total number of tokens in the file.
    """

    embedding: list[float]
    total_tokens: int


class EmbeddingStore(Protocol):
    """
    This class is used to store embeddings as well as retrieve file metadata required for the embedding process.
    """

    async def find_files(
        self,
        white_list: list[str],
        blacklisted_files: list[str],
    ) -> list[FileMetadata]:
        """
        Finds the files that are not yet embedded and are in the white list and not in the black list.
        The reason is that we use ELT instead of ETL, all files are ingested and then filtered
        out based on the white list and black list.

        Args:
            white_list (list[str]): The list of file extensions that are allowed to be embedded.
            blacklisted_files (list[str]): The list of file names that are not allowed to be embedded.

        Returns:
            (list[FileMetadata]): The list of files that are allowed to be embedded.
        """

        ...

    async def save_embeddings(
        self, embeddings: EmbeddingWithCount, metadata: FileMetadata
    ) -> None:
        """
        Saves the embeddings to the database.

        Args:
            embeddings (EmbeddingWithCount): The embeddings to save.
            metadata (FileMetadata): The metadata of the file that was embedded.
        """
        ...


class TextEmbedder(Protocol):
    """
    This class is used to embed text, it takes text and metadata and returns the embedding
    and the total number of tokens in the text.
    """

    async def embed_chunk(
        self,
        chunks: list[str],
        metadata: FileMetadata,
    ) -> list[EmbeddingWithCount]:
        """
        Embeds the text and returns the embeddings and the total number of tokens in the text.

        Args:
            text (str): The code to embed.
            metadata (FileMetadata): The metadata of the file.

        Returns:
            list[EmbeddingWithCount]: The embeddings and the total number of tokens in the text.
        """
        ...


@dataclass(frozen=True, slots=True)
class TextSplitter:
    """
    This class is used to split the text into chunks of 7000 tokens.
    This is necessary because the OpenAI API has a limit of 8000 tokens per request.
    We split the text into chunks of 7000 tokens to account for the tokens used by the metadata.

    Args:
        encoding (Encoding): The encoding to use for tokenization.
    """

    encoding: Encoding = tiktoken.get_encoding("cl100k_base")

    def split_text_to_chunks(self, text: str, name: str) -> list[str]:
        """
        Splits the text into chunks of 7000 tokens.

        Args:
            text (str): The text to split.
            name (str): The name of the file. Used for logging.

        Returns:
            list[str]: The list of chunks.
        """
        tokens = self._count_tokens(text)
        num_chunks = (tokens // 7000) + 1
        char_per_chunk = len(text) // num_chunks
        app_logger.info(
            f"Splitting {name} into {num_chunks} chunks of {char_per_chunk} characters."
        )
        return [
            text[i : i + char_per_chunk]  # noqa E203
            for i in range(0, len(text), char_per_chunk + 1)
            # + 1 is added for empty files
        ]

    def _count_tokens(self, text: str) -> int:
        num_tokens = len(self.encoding.encode(text))
        return num_tokens


@dataclass(frozen=True, slots=True)
class EmbeddingService:
    """
    This class is used to embed files and save the embeddings to the database.

    Args:
        db (EmbeddingStore): The database object that is used to store the embeddings.
        embedder (TextEmbedder): The object that is used to embed the files.
        auth_header (AuthHeader): The authorization header for the API requests.
        blacklisted_files (list[str]): The list of file names that are not allowed to be embedded.
        white_list (list[str]): The list of file extensions that are allowed to be embedded.
        splitter (TextSplitter): The object that is used to split the text into chunks.
    """

    db: EmbeddingStore
    embedder: TextEmbedder
    auth_header: AuthHeader
    blacklisted_files: list[str]
    white_list: list[str]
    splitter: TextSplitter = TextSplitter()

    async def embed_and_persist_files(self) -> None:
        """
        Embeds the files and saves the embeddings to the database.
        We do this in two steps:
        1. Fetch the files from the GitHub API.
        2. Embed the files and save the embeddings to the
        database.
        """

        metadata = await self.db.find_files(self.white_list, self.blacklisted_files)
        file_futures = [self.get_file_content(meta) for meta in metadata]

        file_contents = await asyncio.gather(*file_futures)
        app_logger.info("Fetched all files. Starting to embed.")
        embedding_futures = [
            self.process_and_save(text, metadata)
            for metadata, text in zip(metadata, file_contents)
        ]

        _ = await asyncio.gather(*embedding_futures)

    async def get_file_content(self, metadata: FileMetadata) -> str:
        """
        Fetches the file content from the GitHub API.
        The database doesn't store the content of the file,
        so we need to fetch it from the GitHub API.

        Args:
            metadata (FileMetadata): The metadata of the file to fetch.

        Returns:
            str: The code that is stored in the file.
        """
        app_logger.debug(
            f"Fetching document {metadata.document_id} from {metadata.repository_name}"
        )
        path = metadata.file.content_url
        async with aiohttp.ClientSession(headers=self.auth_header.to_dict()) as session:
            async with session.get(path) as response:
                return await response.text()

    async def process_and_save(
        self,
        text: str,
        metadata: FileMetadata,
    ) -> None:
        """
        Embeds the code and saves the embeddings to the database.
        The metadata is also added while saving the embeddings to add things
        like the file name, extensions, path, repository and so on.

        Args:
            text (str): The code to embed.
            metadata (FileMetadata): The metadata of the file.
        """
        chunks = self.splitter.split_text_to_chunks(text, "test")
        embeddings = await self.embedder.embed_chunk(chunks, metadata)
        save_embeddings = [
            self.db.save_embeddings(embedding, metadata) for embedding in embeddings
        ]
        await asyncio.gather(*save_embeddings)


@dataclass(frozen=True, slots=True)
class OpenAIEmbedder(TextEmbedder):
    """
    A TextEmbedder implementation that uses the OpenAI API to embed text.
    Args:
        api_client (AsyncOpenAI): The OpenAI API client to use.
        embedding_model (str): The name of the embedding model to use.
    """

    api_client: AsyncOpenAI
    embedding_model: str

    async def embed_chunk(
        self,
        chunks: list[str],
        metadata: FileMetadata,
    ) -> list[EmbeddingWithCount]:
        enriched_content = [
            self._enrich_file_content(chunk, metadata.file) for chunk in chunks
        ]
        embeddings = self._embed_document(enriched_content)
        return await embeddings

    def _enrich_file_content(self, file_content: str, file: GitHubFile) -> str:
        file_name = f"\nThe file name is {file.name}.\n"
        file_place_in_project = f"The file is located at {file.path_in_project}.\n"
        file_extension = f"The file extension is {file.extension}.\n"
        return file_content + file_name + file_place_in_project + file_extension

    async def _embed_document(self, text: list[str]) -> list[EmbeddingWithCount]:
        return await self._embed_documents_with_retry(text, 3)

    async def _embed_documents_with_retry(
        self,
        text: list[str],
        max_retries: int,
    ) -> list[EmbeddingWithCount]:
        for attempt in range(max_retries):
            futures: list[Coroutine[Any, Any, CreateEmbeddingResponse]] = []
            try:
                for chunk in text:
                    future = self.api_client.embeddings.create(
                        model=self.embedding_model, input=chunk
                    )
                    futures.append(future)

                responses = await asyncio.gather(*futures)
                embeddings = self._process_responses(responses)
                return embeddings

            except Exception as e:
                app_logger.error(f"Received an internal server error. {attempt}s left")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(5 * attempt + 1)
        else:
            raise RuntimeError("Failed to retrieve embeddings after maximum retries.")

    def _process_responses(self, responses: list[CreateEmbeddingResponse]):
        embeddings: list[EmbeddingWithCount] = []
        for response in responses:
            embedding_vec = response.data[0].embedding
            tokens = response.usage.total_tokens
            embedding = EmbeddingWithCount(embedding_vec, tokens)
            embeddings.append(embedding)
        return embeddings


@dataclass(frozen=True, slots=True)
class EmbeddingPersistence(EmbeddingStore):
    """
    A class that implements the EmbeddingStore protocol.
    It is used to store the embeddings in the database as well as retrieve the
    metadata of the files that are to be embedded.
    """

    session_maker: async_sessionmaker[AsyncSession]

    async def find_files(
        self,
        white_list: list[str],
        blacklisted_files: list[str],
    ) -> list[FileMetadata]:
        query = (
            select(GithubFileModel)
            .where(GithubFileModel.is_embedded.is_(False))
            .where(GithubFileModel.file_extension.in_(white_list))
            .where(GithubFileModel.name.not_in(blacklisted_files))
        )
        async with self.session_maker() as session:
            files = await session.scalars(query)
            files = files.all()
        app_logger.info(f"Found {len(files)} files to embed.")
        github_files = [FileMetadata.from_db_object(file) for file in files]
        return github_files

    async def save_embeddings(
        self, embeddings: EmbeddingWithCount, metadata: FileMetadata
    ) -> None:
        embedded_document = EmbeddedDocumentModel(
            document_id=metadata.document_id,
            embedding=embeddings.embedding,
            input_token_count=embeddings.total_tokens,
        )
        original_file = select(GithubFileModel).where(
            GithubFileModel.id == metadata.document_id
        )
        async with self.session_maker() as session:
            orig = await session.scalar(original_file)
            if orig:
                orig.is_embedded = True
            session.add(embedded_document)
            await session.commit()
