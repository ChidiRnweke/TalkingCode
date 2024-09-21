import logging
import os
from dagster import ConfigurableResource, EnvVar
from pipelines.processing import AppConfig, whitelist_str_as_list
from shared.env import env_var_or_default

log = logging.getLogger("app_logger")


class AppConfigResource(ConfigurableResource):
    github_token: str
    openai_api_key: str
    db_connection_string: str
    whitelisted_extensions: list[str]
    blacklisted_files: list[str]
    embedding_disk_path: str = "embeddings"
    embedding_model: str = "text-embedding-3-large"
    max_embedding_input_length: int = 8000

    @classmethod
    def from_env(cls) -> "AppConfigResource":
        openai_key = EnvVar("OPENAI_EMBEDDING_API_KEY")
        github_key = EnvVar("GITHUB_API_TOKEN")
        conn_str = EnvVar("DATABASE_URL")
        whitelist = env_var_or_default("WHITELISTED_EXTENSIONS", "'[\"py\"]'", log)
        blacklist = env_var_or_default("BLACKLISTED_FILES", "[]", log)

        if os.getenv("DATABASE_URL") is None:
            logging.warning("DATABASE_URL is not set. Using dev configuration.")
            conn_str = "postgresql://postgres:postgres@localhost:5432/chatGITpt"

        whitelist = whitelist_str_as_list(whitelist)
        blacklist = whitelist_str_as_list(blacklist)

        return cls(
            github_token=github_key,
            openai_api_key=openai_key,
            db_connection_string=conn_str,
            whitelisted_extensions=whitelist,
            blacklisted_files=blacklist,
        )

    def get_app_config(self) -> AppConfig:
        return AppConfig(
            github_token=self.github_token,
            openai_api_key=self.openai_api_key,
            db_connection_string=self.db_connection_string,
            embedding_disk_path=self.embedding_disk_path,
            embedding_model=self.embedding_model,
            whitelisted_extensions=self.whitelisted_extensions,
            blacklisted_files=self.blacklisted_files,
            max_embedding_input_length=self.max_embedding_input_length,
        )
