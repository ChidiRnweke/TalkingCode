import json
from dataclasses import dataclass

from talkingcode.shared.env import env_var_or_default, get_env_or_raise


@dataclass(frozen=True)
class QdrantConfig:
    server_mode: bool
    server_url: str
    local_port: int


@dataclass(frozen=True)
class IngestionConfig:
    github_token: str
    openai_api_key: str
    topics_prompt: str
    metadata_enrichment_model: str
    db_connection_string: str
    whitelisted_extensions: list[str]
    blacklisted_files: list[str]
    qdrant_server_mode: bool
    qdrant_server_url: str
    qdrant_local_port: int
    qdrant_collection_name: str
    qdrant_local_storage_path: str

    max_embedding_input_length: int = 8000
    embedding_disk_path: str = "embeddings"
    embedding_model: str = "text-embedding-3-large"

    @classmethod
    def from_env(cls) -> "IngestionConfig":
        github_api_key = get_env_or_raise("GITHUB_API_TOKEN")
        api_key = get_env_or_raise("OPENAI_API_KEY")
        conn_string = env_var_or_default(
            "ASYNC_DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/chatGITpt",
        )
        whitelisted_extensions = env_var_or_default(
            "WHITELISTED_EXTENSIONS", "'[\"py\"]'"
        )
        blacklisted_files = env_var_or_default("BLACKLISTED_FILES", "[]")
        topics_prompt = get_env_or_raise("TOPICS_PROMPT")
        metadata_enrichment_model = get_env_or_raise("METADATA_ENRICHMENT_MODEL")
        qdrant_server_mode = bool(env_var_or_default("QDRANT_SERVER_MODE", "False"))
        qdrant_server_url = env_var_or_default(
            "QDRANT_SERVER_URL", "http://localhost:6333"
        )
        qdrant_local_port = int(env_var_or_default("QDRANT_LOCAL_PORT", "6333"))
        qdrant_collection_name = get_env_or_raise("QDRANT_COLLECTION_NAME")
        qdrant_local_storage_path = env_var_or_default(
            "QDRANT_LOCAL_STORAGE_PATH", "../qdrant-data"
        )

        whitelisted_extensions = whitelist_str_as_list(whitelisted_extensions)
        blacklisted_files = whitelist_str_as_list(blacklisted_files)

        return cls(
            github_token=github_api_key,
            openai_api_key=api_key,
            db_connection_string=conn_string,
            whitelisted_extensions=whitelisted_extensions,
            blacklisted_files=blacklisted_files,
            topics_prompt=topics_prompt,
            metadata_enrichment_model=metadata_enrichment_model,
            qdrant_server_mode=qdrant_server_mode,
            qdrant_server_url=qdrant_server_url,
            qdrant_local_port=qdrant_local_port,
            qdrant_collection_name=qdrant_collection_name,
            qdrant_local_storage_path=qdrant_local_storage_path,
        )


def whitelist_str_as_list(whitelisted_extensions: str) -> list[str]:
    try:
        whitelist = json.loads(whitelisted_extensions)
    except json.JSONDecodeError:
        raise ValueError(
            'WHITELISTED_EXTENSIONS must be a valid JSON array of strings. Example: \'["py", "java"]\''
        )

    return whitelist
