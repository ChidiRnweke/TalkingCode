import os
from dataclasses import dataclass
from github import Auth, Github
from .ingestion import save_and_persist_data


__all__ = ["AppConfig", "save_and_persist_data"]


@dataclass(frozen=True)
class AppConfig:
    api_key: str

    @staticmethod
    def from_env():
        api_key = os.getenv("GITHUB_API_TOKEN")
        if api_key is None:
            raise ValueError("API_KEY is not set and is required to run the pipeline.")
        return AppConfig(api_key=api_key)

    def get_github_client(self) -> Github:
        auth = Auth.Token(self.api_key)
        return Github(auth=auth)
