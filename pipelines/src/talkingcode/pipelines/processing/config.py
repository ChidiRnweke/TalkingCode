from dataclasses import dataclass
import json

from openai import AsyncOpenAI
from pipelines.processing.ingestion import GithubHTTPClient
from pipelines.processing.models import AuthHeader
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from shared.env import env_var_or_default, get_env_or_raise


@dataclass(frozen=True)
class IngestionConfig:
    github_token: str
    openai_api_key: str
    db_connection_string: str
    whitelisted_extensions: list[str]
    blacklisted_files: list[str]

    max_embedding_input_length: int = 8000
    embedding_disk_path: str = "embeddings"
    embedding_model: str = "text-embedding-3-large"

    @staticmethod
    def from_env() -> "IngestionConfig":
        github_api_key = get_env_or_raise("GITHUB_API_TOKEN")
        api_key = get_env_or_raise("OPENAI_EMBEDDING_API_KEY")
        conn_string = env_var_or_default(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/chatGITpt",
        )
        whitelisted_extensions = env_var_or_default(
            "WHITELISTED_EXTENSIONS", "'[\"py\"]'"
        )
        blacklisted_files = env_var_or_default("BLACKLISTED_FILES", "[]")

        whitelisted_extensions = whitelist_str_as_list(whitelisted_extensions)
        blacklisted_files = whitelist_str_as_list(blacklisted_files)

        return IngestionConfig(
            github_token=github_api_key,
            openai_api_key=api_key,
            db_connection_string=conn_string,
            whitelisted_extensions=whitelisted_extensions,
            blacklisted_files=blacklisted_files,
        )

    def get_github_client(self) -> GithubHTTPClient:
        auth_header = AuthHeader(Authorization="Authorization", token=self.github_token)
        return GithubHTTPClient(auth_header)

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        engine = create_async_engine(self.db_connection_string)
        Session = async_sessionmaker(engine, expire_on_commit=False)
        return Session

    def get_openai_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=self.openai_api_key)


def whitelist_str_as_list(whitelisted_extensions: str) -> list[str]:
    try:
        whitelist = json.loads(whitelisted_extensions)
    except json.JSONDecodeError:
        raise ValueError(
            'WHITELISTED_EXTENSIONS must be a valid JSON array of strings. Example: \'["py", "java"]\''
        )

    return whitelist
