import logging
from dagster import ConfigurableResource, EnvVar
from src.processing import AppConfig, whitelist_str_as_list


class AppConfigResource(ConfigurableResource):
    github_token: str
    openai_api_key: str
    db_connection_string: str
    whitelisted_extensions: list[str]
    embedding_disk_path: str = "embeddings"
    model: str = "text-embedding-3-large"

    @classmethod
    def from_env(cls) -> "AppConfigResource":
        openai_key = EnvVar("OPENAI_EMBEDDING_API_KEY").get_value()
        github_key = EnvVar("GITHUB_API_TOKEN").get_value()
        conn_str = EnvVar("DATABASE_URL").get_value()
        whitelist = EnvVar("WHITELISTED_EXTENSIONS").get_value()

        if openai_key is None:
            raise ValueError(
                "OPENAI_EMBEDDING_API_KEY is not set and is required to run the pipeline."
            )

        if github_key is None:
            raise ValueError(
                "GITHUB_API_TOKEN is not set and is required to run the pipeline."
            )

        if conn_str is None:
            logging.warning("DATABASE_URL is not set. Using dev configuration.")
            conn_str = "postgresql://postgres:postgres@localhost:5432/chatGITpt"

        if whitelist is None:
            raise ValueError(
                "WHITELISTED_EXTENSIONS is not set and is required to run the pipeline."
            )

        whitelist = whitelist_str_as_list(whitelist)

        return cls(
            github_token=github_key,
            openai_api_key=openai_key,
            db_connection_string=conn_str,
            whitelisted_extensions=whitelist,
        )

    def get_app_config(self) -> AppConfig:
        return AppConfig(
            github_token=self.github_token,
            openai_api_key=self.openai_api_key,
            db_connection_string=self.db_connection_string,
            embedding_disk_path=self.embedding_disk_path,
            model=self.model,
            whitelisted_extensions=self.whitelisted_extensions,
        )
