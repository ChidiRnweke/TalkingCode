from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.github_client import GithubHTTPClient
from talkingcode.shared import get_qdrant_client

from .embedding import OpenAIEmbedder, TextSplitter
from .metadata_enrichment import MetadataEnricher, TopicsEnrichment
from .metadata_storage import MetadataStorageService
from .transformation_pipeline import TransformationPipeline
from .vector_storage import QdrantVectorStore


def from_config(config: IngestionConfig) -> TransformationPipeline:
    embedder = embedder_from_config(config)
    metadata_store = metadata_storage_from_config(config)
    github = GithubHTTPClient.from_config(config)
    qdrant_store = qdrant_vector_store_from_config(config)
    topics_enrichment = topics_enrichment_from_config(config)
    metadata_enricher = MetadataEnricher()
    return TransformationPipeline(
        file_transformations=[topics_enrichment, metadata_enricher],
        metadata_store=metadata_store,
        embedder=embedder,
        github=github,
        payload_store=qdrant_store,
    )


def embedder_from_config(config: IngestionConfig) -> OpenAIEmbedder:
    client = AsyncOpenAI(api_key=config.openai_api_key)
    github = GithubHTTPClient.from_config(config)
    return OpenAIEmbedder(client, TextSplitter(), github, config.embedding_model)


def topics_enrichment_from_config(config: IngestionConfig) -> TopicsEnrichment:
    client = AsyncOpenAI(api_key=config.openai_api_key)
    return TopicsEnrichment(
        client,
        config.topics_prompt,
        config.metadata_enrichment_model,
    )


def qdrant_vector_store_from_config(config: IngestionConfig) -> QdrantVectorStore:
    server_mode = config.qdrant_server_mode
    metadata_store = metadata_storage_from_config(config)
    collection_name = config.qdrant_collection_name
    local_storage = config.qdrant_local_storage_path
    client = get_qdrant_client(
        server_mode=server_mode,
        server_url=config.qdrant_server_url,
        api_key=config.qdrant_api_key,
        local_storage_path=local_storage,
    )
    return QdrantVectorStore(client, metadata_store, collection_name)


def metadata_storage_from_config(config: IngestionConfig) -> MetadataStorageService:
    """
    Factory method to create an instance of the `MetadataStorageService` class from a configuration object.
    This is a helper function used by the `from_config` method.

    Args:
        config (IngestionConfig): The configuration object to use for creating the service.

    Returns:
        MetadataStorageService: An instance of the `MetadataStorageService` class.
    """
    sync_mode = "sqlite" in config.db_connection_string
    if "asyncpg" in config.db_connection_string:
        connection_args = {"server_settings": {"search_path": "ingestion"}}
        engine = create_async_engine(
            config.db_connection_string,
            connect_args=connection_args,
        )
    else:
        engine = create_async_engine(config.db_connection_string)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    return MetadataStorageService(
        session=Session,
        allowed_extensions=config.allowed_extensions,
        disallowed_files=config.skipped_files,
        sync_mode=sync_mode,
    )


__all__ = ["from_config"]
