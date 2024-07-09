from dataclasses import dataclass
from github import Auth, Github
from openai import AsyncOpenAI
from sqlalchemy import create_engine
from .ingestion import IngestionService, DatabaseService
from .embedding import AuthHeader, EmbeddingService, EmbeddingPersistence, TextEmbedder
import logging
import json
from shared.env import env_var_or_default, env_var_or_throw
from sqlalchemy.orm import sessionmaker, Session

__all__ = [
    "AppConfig",
    "IngestionService",
    "DatabaseService",
    "EmbeddingService",
    "whitelist_str_as_list",
    "AuthHeader",
    "EmbeddingPersistence",
    "TextEmbedder",
]

log = logging.getLogger("app_logger")


@dataclass(frozen=True)
class AppConfig:
    github_token: str
    openai_api_key: str
    db_connection_string: str
    whitelisted_extensions: list[str]
    blacklisted_files: list[str]

    max_embedding_input_length: int = 8000
    embedding_disk_path: str = "embeddings"
    embedding_model: str = "text-embedding-3-large"

    @staticmethod
    def from_env() -> "AppConfig":
        github_api_key = env_var_or_throw("GITHUB_API_TOKEN", log)
        api_key = env_var_or_throw("OPENAI_EMBEDDING_API_KEY", log)
        conn_string = env_var_or_default(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/chatGITpt",
            log,
        )
        whitelisted_extensions = env_var_or_default(
            "WHITELISTED_EXTENSIONS", "'[\"py\"]'", log
        )
        blacklisted_files = env_var_or_default("BLACKLISTED_FILES", "[]", log)

        whitelisted_extensions = whitelist_str_as_list(whitelisted_extensions)
        blacklisted_files = whitelist_str_as_list(blacklisted_files)

        return AppConfig(
            github_token=github_api_key,
            openai_api_key=api_key,
            db_connection_string=conn_string,
            whitelisted_extensions=whitelisted_extensions,
            blacklisted_files=blacklisted_files,
        )

    def get_github_client(self) -> Github:
        auth = Auth.Token(self.github_token)
        return Github(auth=auth)

    def get_session_maker(self) -> sessionmaker[Session]:
        engine = create_engine(self.db_connection_string, echo=True)
        Session = sessionmaker(engine)
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
