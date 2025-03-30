from talkingcode.backend.config import AppConfig
from talkingcode.shared.qdrant_client_factory import get_qdrant_client

from .generation import InputQuery, OpenAIGenerationService
from .keyword_identifier import KeywordIdentifier, KeywordIdentifierService
from .rag import RetrievalAugmentedGeneration
from .retrieve import (
    OpenAIEmbeddingService,
    QdrantFilterRetrievalService,
    RemainingSpend,
    RetrievalService,
)
from .token_spend import SQLTokenStore


def vector_store_from_config(config: AppConfig) -> RetrievalService:
    server_mode = config.qdrant_server_mode
    collection_name = config.qdrant_collection_name

    client = get_qdrant_client(
        server_mode=server_mode,
        server_url=config.qdrant_server_url,
        api_key=config.qdrant_api_key,
        local_storage_path=config.qdrant_local_storage_path,
    )

    return QdrantFilterRetrievalService(client, config.top_k, collection_name)


__all__ = [
    "RetrievalAugmentedGeneration",
    "InputQuery",
    "OpenAIEmbeddingService",
    "OpenAIGenerationService",
    "RetrievalService",
    "RemainingSpend",
    "vector_store_from_config",
    "SQLTokenStore",
    "KeywordIdentifier",
    "KeywordIdentifierService",
]
