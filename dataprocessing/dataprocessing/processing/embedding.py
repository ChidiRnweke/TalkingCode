import asyncio
import logging
from openai import AsyncOpenAI
from typing import Any, Coroutine, Self
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from shared.database import GithubFileModel, EmbeddedDocumentModel
from dataprocessing.processing.ingestion import GitHubFile
from dataclasses import dataclass
import aiohttp
import tiktoken
from tiktoken import Encoding
from openai.types import CreateEmbeddingResponse

app_logger = logging.getLogger("app_logger")


@dataclass(frozen=True)
class FileMetadata:
    repository_name: str
    document_id: int
    file: GitHubFile

    @classmethod
    def from_db_object(cls, file: GithubFileModel) -> Self:
        return cls(
            repository_name=file.repository_name,
            document_id=file.id,
            file=GitHubFile.from_db_object(file),
        )


@dataclass(frozen=True)
class EmbeddingWithCount:
    embedding: list[float]
    total_tokens: int


@dataclass(frozen=True)
class AuthHeader:
    Authorization: str
    token: str

    def to_dict(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


@dataclass(frozen=True)
class TextSplitter:
    encoding: Encoding = tiktoken.get_encoding("cl100k_base")

    def split_text_to_chunks(self, text: str, name: str) -> list[str]:
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


@dataclass(frozen=True)
class EmbeddingService:
    db: "EmbeddingPersistance"
    embedder: "TextEmbedder"
    auth_header: AuthHeader
    blacklisted_files: list[str]
    white_list: list[str]
    splitter: TextSplitter = TextSplitter()

    async def embed_and_persist_files(self) -> None:

        metadata = self.db.find_files(self.white_list, self.blacklisted_files)
        file_futures = [self.get_file_content(meta) for meta in metadata]

        file_contents = await asyncio.gather(*file_futures)
        app_logger.info("Fetched all files. Starting to embed.")
        embedding_futures = [
            self.process_and_save(text, metadata)
            for metadata, text in zip(metadata, file_contents)
        ]

        _ = await asyncio.gather(*embedding_futures)

    async def get_file_content(self, metadata: FileMetadata) -> str:
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
        chunks = self.splitter.split_text_to_chunks(text, "test")
        embeddings = await self.embedder.embed_chunk(chunks, metadata)
        for embedding in embeddings:
            self.db.save_embeddings(embedding, metadata)


@dataclass(frozen=True)
class TextEmbedder:
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


@dataclass(frozen=True)
class EmbeddingPersistance:
    session_maker: sessionmaker[Session]

    def find_files(
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
        with self.session_maker() as session:
            files = session.scalars(query).all()
        app_logger.info(f"Found {len(files)} files to embed.")
        github_files = [FileMetadata.from_db_object(file) for file in files]
        return github_files

    def save_embeddings(
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
        with self.session_maker() as session:
            orig = session.execute(original_file).scalar()
            if orig:
                orig.is_embedded = True
            session.add(embedded_document)
            session.commit()
