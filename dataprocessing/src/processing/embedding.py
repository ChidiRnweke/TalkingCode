import asyncio
import logging
from openai import AsyncOpenAI
from typing import Coroutine, Self, Any
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from src.processing.database import GithubFileModel, EmbeddedDocumentModel
from src.processing.ingestion import GitHubFile
from dataclasses import dataclass, asdict
import json
from openai import InternalServerError
import aiohttp

EMBEDDING_MAX_CHARACTERS = 8000
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


def split_text_to_chunks(text: str, max_characters: int) -> list[str]:
    return [
        text[i : i + max_characters]  # noqa: E203
        for i in range(0, len(text), max_characters)
    ]


async def embed_and_persist_files(
    session_maker: sessionmaker[Session],
    white_list: list[str],
    api_client: AsyncOpenAI,
    github_client: AuthHeader,
    model: str,
    embeddings_disk_path: str,
) -> None:
    """
    Process files by retrieving their content from GitHub, enriching the content,
    embedding the documents, and persisting the embeddings to disk and database.

    Args:
        session_maker (sessionmaker[Session]): The session maker for the database.
        api_client (AsyncOpenAI): The API client for embedding documents.
        github_client (Github): The GitHub client for retrieving file content.
        model (embedding_model_type): The embedding model to use for embedding documents.
        embeddings_disk_path (str): The path to save the embeddings to disk.

    """

    file_metadata_list = find_files(session_maker, white_list)
    embedding_futures: list[list[Coroutine[Any, Any, EmbeddingWithCount]]] = []
    file_content_futures = [
        get_file_content(github_client, metadata) for metadata in file_metadata_list
    ]
    file_contents = await asyncio.gather(*file_content_futures)
    for file_content, metadata in zip(file_contents, file_metadata_list):
        chunked_input = split_text_to_chunks(file_content, EMBEDDING_MAX_CHARACTERS)
        embeddings = [
            embed_chunk(chunk, metadata, api_client, model) for chunk in chunked_input
        ]
        embedding_futures.append(embeddings)

    embeddings_with_count = await asyncio.gather(
        *(asyncio.gather(*sublist) for sublist in embedding_futures)
    )
    for embeddings, metadata in zip(embeddings_with_count, file_metadata_list):
        for chunk in embeddings:
            persist_embeddings_to_disk(embeddings_disk_path, chunk, metadata)
            try:
                save_embeddings_to_db(session_maker, chunk, metadata)
            except Exception as e:
                app_logger.error(f"Failed to save embeddings to database: {e}")


async def embed_chunk(
    file_content: str, metadata: FileMetadata, api_client: AsyncOpenAI, model: str
) -> EmbeddingWithCount:
    enriched_content = enrich_file_content(file_content, metadata.file)
    embeddings = embed_document(api_client, enriched_content, model)
    return await embeddings


def persist_embeddings_to_disk(
    file_path: str,
    embeddings: EmbeddingWithCount,
    metadata: FileMetadata,
) -> None:
    metadata_json = asdict(metadata)
    metadata_json["embedding"] = embeddings.embedding
    metadata_json["input_token_count"] = embeddings.total_tokens
    metadata_json["repository_name"] = metadata.repository_name
    metadata_json["document_id"] = metadata.document_id
    write_path = file_path + f"/{metadata.repository_name}_{metadata.document_id}.json"
    with open(write_path, "w") as file:
        json.dump(metadata_json, file)


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
) -> list[FileMetadata]:
    query = (
        select(GithubFileModel)
        .where(GithubFileModel.is_embedded.is_(False))
        .where(GithubFileModel.file_extension.in_(white_list))
    )
    with session_maker() as session:
        files = session.scalars(query).all()
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
    openai_client: AsyncOpenAI, text: str, model: str
) -> EmbeddingWithCount:
    return await embed_documents_with_retry(openai_client, text, model, 3)


async def embed_documents_with_retry(
    openai_client: AsyncOpenAI,
    text: str,
    model: str,
    max_retries: int,
) -> EmbeddingWithCount:
    for attempt in range(max_retries):
        try:
            response = await openai_client.embeddings.create(input=[text], model=model)
            embedding = response.data[0].embedding
            total_tokens = response.usage.total_tokens
            return EmbeddingWithCount(embedding, total_tokens)
        except Exception as e:
            app_logger.error(f"Received an internal server error. {attempt}s left")
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(5 * attempt + 1)
    else:
        raise RuntimeError("Failed to retrieve embeddings after maximum retries.")
