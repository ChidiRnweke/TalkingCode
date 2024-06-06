import asyncio
import logging
from openai import AsyncOpenAI
from typing import Self
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from shared.database import GithubFileModel, EmbeddedDocumentModel
from dataprocessing.processing.ingestion import GitHubFile
from dataclasses import dataclass
import aiohttp
import tiktoken

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


def count_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = len(encoding.encode(text))
    return num_tokens


def split_text_to_chunks(text: str, name: str) -> list[str]:
    tokens = count_tokens(text)
    num_chunks = (tokens // 7000) + 1
    char_per_chunk = len(text) // num_chunks
    app_logger.info(
        f"Splitting {name} into {num_chunks} chunks of {char_per_chunk} characters."
    )
    return [
        text[i : i + char_per_chunk]  # noqa E203
        for i in range(0, len(text), char_per_chunk + 1)  # + 1 is added for empty files
    ]


async def embed_and_persist_files(
    session_maker: sessionmaker[Session],
    white_list: list[str],
    api_client: AsyncOpenAI,
    auth_header: AuthHeader,
    model: str,
    max_characters: int,
    blacklisted_files: list[str],
) -> None:

    file_metadata_list = find_files(session_maker, white_list, blacklisted_files)
    file_content_futures = [
        get_file_content(auth_header, metadata) for metadata in file_metadata_list
    ]

    file_contents = await asyncio.gather(*file_content_futures)
    app_logger.info("Fetched all files. Starting to embed.")
    embedding_futures = [
        embed_chunk(
            split_text_to_chunks(file_content, metadata.file.name),
            metadata,
            api_client,
            model,
        )
        for file_content, metadata in zip(file_contents, file_metadata_list)
    ]

    embeddings_with_count = await asyncio.gather(*embedding_futures)
    for embedded_file, metadata in zip(embeddings_with_count, file_metadata_list):
        for chunk in embedded_file:
            try:
                save_embeddings_to_db(session_maker, chunk, metadata)
            except Exception as e:
                app_logger.error(f"Failed to save embeddings to database: {e}")


async def embed_chunk(
    chunks: list[str], metadata: FileMetadata, api_client: AsyncOpenAI, model: str
) -> list[EmbeddingWithCount]:
    enriched_content = [enrich_file_content(chunk, metadata.file) for chunk in chunks]
    embeddings = embed_document(api_client, enriched_content, model)
    return await embeddings


def save_embeddings_to_db(
    session_maker: sessionmaker[Session],
    embeddings: EmbeddingWithCount,
    metadata: FileMetadata,
) -> None:
    embedded_document = EmbeddedDocumentModel(
        document_id=metadata.document_id,
        embedding=embeddings.embedding,
        input_token_count=embeddings.total_tokens,
    )
    with session_maker() as session:
        session.add(embedded_document)
        session.commit()


def find_files(
    session_maker: sessionmaker[Session],
    white_list: list[str],
    blacklisted_files: list[str],
) -> list[FileMetadata]:
    query = (
        select(GithubFileModel)
        .where(GithubFileModel.is_embedded.is_(False))
        .where(GithubFileModel.file_extension.in_(white_list))
        .where(GithubFileModel.name.not_in(blacklisted_files))
    )
    with session_maker() as session:
        files = session.scalars(query).all()
    app_logger.info(f"Found {len(files)} files to embed.")
    github_files = [FileMetadata.from_db_object(file) for file in files]
    return github_files


async def get_file_content(auth: AuthHeader, metadata: FileMetadata) -> str:
    app_logger.debug(
        f"Fetching document {metadata.document_id} from {metadata.repository_name}"
    )
    path = metadata.file.content_url
    async with aiohttp.ClientSession(headers=auth.to_dict()) as session:
        async with session.get(path) as response:
            return await response.text()


def enrich_file_content(file_content: str, file: GitHubFile) -> str:
    file_name = f"\nThe file name is {file.name}.\n"
    file_place_in_project = f"The file is located at {file.path_in_project}.\n"
    file_extension = f"The file extension is {file.extension}.\n"
    return file_content + file_name + file_place_in_project + file_extension


async def embed_document(
    openai_client: AsyncOpenAI, text: list[str], model: str
) -> list[EmbeddingWithCount]:
    return await embed_documents_with_retry(openai_client, text, model, 3)


async def embed_documents_with_retry(
    openai_client: AsyncOpenAI,
    text: list[str],
    model: str,
    max_retries: int,
) -> list[EmbeddingWithCount]:
    for attempt in range(max_retries):
        try:
            responses = await asyncio.gather(
                *[
                    openai_client.embeddings.create(model=model, input=chunk)
                    for chunk in text
                ]
            )
            embeddings = [
                EmbeddingWithCount(
                    response.data[0].embedding, response.usage.total_tokens
                )
                for response in responses
            ]
            return embeddings
        except Exception as e:
            app_logger.error(f"Received an internal server error. {attempt}s left")
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(5 * attempt + 1)
    else:
        raise RuntimeError("Failed to retrieve embeddings after maximum retries.")
