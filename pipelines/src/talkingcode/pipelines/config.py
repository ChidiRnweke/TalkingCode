import json
from dataclasses import dataclass

from talkingcode.shared.environment import SecretsReader

from .default_prompts import metadata_prompt


@dataclass(frozen=True, slots=True)
class QdrantConfig:
    server_mode: bool
    server_url: str
    local_port: int


@dataclass(frozen=True, slots=True)
class IngestionConfig:
    github_token: str
    openai_api_key: str
    topics_prompt: str
    metadata_enrichment_model: str
    db_connection_string: str
    migrations_connection_string: str
    allowed_extensions: list[str]
    skipped_files: list[str]
    qdrant_server_mode: bool
    qdrant_server_url: str
    qdrant_local_port: int
    qdrant_collection_name: str
    qdrant_local_storage_path: str
    qdrant_api_key: str

    max_embedding_input_length: int = 8000
    embedding_disk_path: str = "embeddings"
    embedding_model: str = "text-embedding-3-large"

    @classmethod
    def from_env(cls) -> "IngestionConfig":
        reader = SecretsReader.from_env()

        github_api_key = reader.read_secret("GITHUB_API_TOKEN")
        api_key = reader.read_secret("OPENAI_API_KEY")
        conn_string = reader.read_or_default(
            "ASYNC_DATABASE_URL", "sqlite+aiosqlite:///talkingcode.sqlite"
        )
        migrations_connection_string = reader.read_or_default(
            "MIGRATIONS_CONNECTION_STRING", "sqlite:///talkingcode.sqlite"
        )
        allowed_extensions = reader.read_secret("WHITELISTED_EXTENSIONS")

        skipped_files = reader.read_secret("BLACKLISTED_FILES")
        topics_prompt = reader.read_or_default("TOPICS_PROMPT", metadata_prompt)
        metadata_enrichment_model = reader.read_secret("METADATA_ENRICHMENT_MODEL")
        qdrant_server_mode = bool(reader.read_optional("QDRANT_SERVER_MODE"))
        qdrant_server_url = reader.read_or_default(
            "QDRANT_SERVER_URL", "http://localhost:6333"
        )
        qdrant_local_port = int(reader.read_or_default("QDRANT_LOCAL_PORT", "6333"))
        qdrant_collection_name = reader.read_or_default(
            "QDRANT_COLLECTION_NAME", "talkingcode"
        )
        qdrant_local_storage_path = reader.read_or_default(
            "QDRANT_LOCAL_STORAGE_PATH", "../qdrant-data"
        )
        qdrant_api_key = reader.read_secret("QDRANT_API_KEY")

        allowed_extensions = strings_to_list(allowed_extensions)
        skipped_files = strings_to_list(skipped_files)

        return cls(
            github_token=github_api_key,
            openai_api_key=api_key,
            db_connection_string=conn_string,
            allowed_extensions=allowed_extensions,
            skipped_files=skipped_files,
            migrations_connection_string=migrations_connection_string,
            topics_prompt=topics_prompt,
            metadata_enrichment_model=metadata_enrichment_model,
            qdrant_server_mode=qdrant_server_mode,
            qdrant_server_url=qdrant_server_url,
            qdrant_local_port=qdrant_local_port,
            qdrant_collection_name=qdrant_collection_name,
            qdrant_local_storage_path=qdrant_local_storage_path,
            qdrant_api_key=qdrant_api_key,
        )


def strings_to_list(string_list: str) -> list[str]:
    try:
        _list = json.loads(string_list)
    except json.JSONDecodeError:
        raise ValueError(
            f'{string_list} must be a valid JSON array of strings. Example: \'["py", "java"]\''
        )

    return _list
