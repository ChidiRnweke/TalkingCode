import os
from dataclasses import dataclass
from github import Auth, Github
from .ingestion import save_and_persist_data
from .embedding import embed_and_persist_files, AuthHeader
import logging
import json

__all__ = [
    "AppConfig",
    "save_and_persist_data",
    "embed_and_persist_files",
    "whitelist_str_as_list",
    "AuthHeader",
]


@dataclass(frozen=True)
class AppConfig:
    github_token: str
    openai_api_key: str
    db_connection_string: str
    whitelisted_extensions: list[str]

    embedding_disk_path: str = "embeddings"
    embedding_model: str = "text-embedding-3-large"

    @staticmethod
    def from_env() -> "AppConfig":
        github_api_key = os.getenv("GITHUB_API_TOKEN")
        api_key = os.getenv("OPENAI_EMBEDDING_API_KEY")
        conn_string = os.getenv("DATABASE_URL")
        whitelisted_extensions = os.getenv("WHITELISTED_EXTENSIONS")

        if conn_string is None:
            logging.warning("DATABASE_URL is not set. Using dev configuration.")
            conn_string = "postgresql://postgres:postgres@localhost:5432/chatGITpt"
        else:
            conn_string = os.path.expandvars(conn_string)

        if whitelisted_extensions is None:
            raise ValueError(
                "WHITELISTED_EXTENSIONS is not set and is required to run the pipeline."
            )

        whitelisted_extensions = whitelist_str_as_list(whitelisted_extensions)

        if github_api_key is None:
            raise ValueError(
                "GITHUB_API_TOKEN is not set and is required to run the pipeline."
            )
        if api_key is None:
            raise ValueError(
                "OPENAI_EMBEDDING_API_KEY is not set and is required to run the pipeline."
            )

        return AppConfig(
            github_token=github_api_key,
            openai_api_key=api_key,
            db_connection_string=conn_string,
            whitelisted_extensions=whitelisted_extensions,
        )

    def get_github_client(self) -> Github:
        auth = Auth.Token(self.github_token)
        return Github(auth=auth)


def whitelist_str_as_list(whitelisted_extensions: str) -> list[str]:
    try:
        whitelist = json.loads(whitelisted_extensions)
    except json.JSONDecodeError:
        raise ValueError(
            'WHITELISTED_EXTENSIONS must be a valid JSON array of strings. Example: \'["py", "java"]\''
        )

    return whitelist
