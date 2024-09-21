import logging
import os
from dagster import ConfigurableResource, EnvVar
from pipelines.processing import AppConfig, whitelist_str_as_list
from shared.env import env_var_or_default

log = logging.getLogger("app_logger")


class AppConfigResource(ConfigurableResource):
    """
    Resource class for the application configuration. It is used by the Dagster
    framework to inject the application configuration into the asset functions.

    Args:
        github_token (str): The GitHub API token.
        openai_api_key (str): The OpenAI API key.
        db_connection_string (str): The database connection string.
        whitelisted_extensions (list[str]): The list of whitelisted file extensions.
            These extensions will be used to filter the files fetched from the GitHub API.
        blacklisted_files (list[str]): The list of blacklisted file names.
            These files will be ignored when fetching data from the GitHub API.
        embedding_disk_path (str): The path to the disk where the embeddings are stored.
         The embeddings are temporarily stored on disk before being persisted to the database.
        embedding_model (str): The OpenAI model used for text embedding.
        max_embedding_input_length (int): The maximum length of the input text for embedding.
    """

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
        """
        Create an instance of the AppConfigResource class from the environment variables.

        Returns:
            AppConfigResource: The application configuration resource.
        """
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
        """
        Get an instance of the AppConfig class from the resource configuration. This is
        because the actual code lives apart from the Dagster framework, and the AppConfig
        class is used in application code.

        Returns:
            AppConfig: The application configuration.
        """
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
