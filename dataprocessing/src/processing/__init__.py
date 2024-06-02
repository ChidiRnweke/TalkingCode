import os
from dataclasses import dataclass
from github import Auth, Github
from .ingestion import save_and_persist_data
import logging

__all__ = ["AppConfig", "save_and_persist_data"]


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str
    db_connection_string: str

    @staticmethod
    def from_env() -> "AppConfig":
        api_key = os.getenv("GITHUB_API_TOKEN")
        conn_string = os.getenv("DATABASE_URL")

        if conn_string is None:
            logging.warning("DATABASE_URL is not set. Using dev configuration.")
            conn_string = "postgresql://postgres:postgres@localhost:5432/chatGITpt"
        else:
            conn_string = os.path.expandvars(conn_string)

        if api_key is None:
            raise ValueError("API_KEY is not set and is required to run the pipeline.")

        return AppConfig(openai_api_key=api_key, db_connection_string=conn_string)

    def get_github_client(self) -> Github:
        auth = Auth.Token(self.openai_api_key)
        return Github(auth=auth)
