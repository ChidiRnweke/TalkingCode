from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.github_client import GithubHTTPClient

from .ingestion import MetadataIngestionService
from .storage import DatabaseService


def from_config(config: IngestionConfig) -> MetadataIngestionService:
    """
    Factory method to create an instance of the `MetadataIngestionService` class from a configuration object.
    This is the main entry point for the `metadata_ingestion` module.

    Args:
        config (IngestionConfig): The configuration object to use for creating the service.

    Returns:
        IngestionService: An instance of the `IngestionService` class.
    """
    sync_mode = "sqlite" in config.db_connection_string
    db = database_service_from_config(config)
    client = GithubHTTPClient.from_config(config)
    return MetadataIngestionService(db=db, client=client, sync_mode=sync_mode)


def database_service_from_config(config: IngestionConfig) -> DatabaseService:
    """
    Factory method to create an instance of the `DatabaseService` class from a configuration object.
    This is a helper function used by the `from_config` method.

    Args:
        config (IngestionConfig): The configuration object to use for creating the service.

    Returns:
        DatabaseService: An instance of the `DatabaseService` class.
    """
    engine = create_async_engine(config.db_connection_string)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    return DatabaseService(session_maker=Session)


__all__ = ["MetadataIngestionService", "from_config"]
