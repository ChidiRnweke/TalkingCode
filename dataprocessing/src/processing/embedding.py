import asyncio
import logging
from github import Github
from github.ContentFile import ContentFile
from openai import AsyncOpenAI
from typing import Coroutine, cast, Self, Any
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker, Session
from src.processing.database import GithubFileModel, EmbeddedDocumentModel
from src.processing.ingestion import GitHubFile
from dataclasses import dataclass, asdict
import json


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


async def embed_and_persist_files(
    session_maker: sessionmaker[Session],
    api_client: AsyncOpenAI,
    github_client: Github,
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
    file_metadata_list = find_files(session_maker)
    embedding_futures: list[Coroutine[Any, Any, EmbeddingWithCount]] = []
    for metadata in file_metadata_list:
        file_content = get_file_content(github_client, metadata)
        enriched_content = enrich_file_content(file_content, metadata.file)
        embeddings = embed_document(api_client, enriched_content, model)
        embedding_futures.append(embeddings)

    embeddings_with_count = await asyncio.gather(*embedding_futures)
    for embeddings, metadata in zip(embeddings_with_count, file_metadata_list):
        persist_embeddings_to_disk(embeddings_disk_path, embeddings, metadata)
        try:
            save_embeddings_to_db(session_maker, embeddings, metadata)
        except Exception as e:
            logging.error(f"Failed to save embeddings to database: {e}")


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


def find_files(session_maker: sessionmaker[Session]) -> list[FileMetadata]:
    query = select(GithubFileModel).where(GithubFileModel.is_embedded.is_(False))
    with session_maker() as session:
        files = session.scalars(query).all()
    github_files = [FileMetadata.from_db_object(file) for file in files]
    return github_files


def get_file_content(github_client: Github, metadata: FileMetadata) -> str:
    repository_name = metadata.repository_name
    content_url = metadata.file.content_url
    file = github_client.get_repo(repository_name).get_contents(content_url)
    file = cast(ContentFile, file)
    file_content = file.decoded_content.decode("utf-8")
    return file_content


def enrich_file_content(file_content: str, file: GitHubFile) -> str:
    file_name = f"\nThe file name is {file.name}.\n"
    file_place_in_project = f"The file is located at {file.path_in_project}.\n"
    file_extension = f"The file extension is {file.extension}.\n"
    return file_content + file_name + file_place_in_project + file_extension


async def embed_document(
    openai_client: AsyncOpenAI, text: str, model: str
) -> EmbeddingWithCount:
    embeddings = await openai_client.embeddings.create(input=[text], model=model)
    embedding = embeddings.data[0].embedding
    total_tokens = embeddings.usage.total_tokens
    return EmbeddingWithCount(embedding, total_tokens)
