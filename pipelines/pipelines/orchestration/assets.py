from dagster import asset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pipelines.orchestration.resources import AppConfigResource
from pipelines.processing import (
    AppConfig,
    IngestionService,
    DatabaseService,
    AuthHeader,
    EmbeddingService,
    OpenAIEmbedder,
    EmbeddingPersistence,
)


def get_session(app: AppConfig) -> sessionmaker[Session]:
    """
    Create a sessionmaker for the database connection.

    Args:
        app (AppConfig): The application configuration.
        Contains the database connection string.

    Returns:
        sessionmaker[Session]: The sessionmaker for the database connection.
    """
    engine = create_engine(app.db_connection_string, echo=True)
    Session = sessionmaker(engine)
    return Session


@asset
def persist_data(app_config_resource: AppConfigResource) -> None:
    """
    Persist data from the GitHub API to the database.

    Args:
        app_config_resource (AppConfigResource): The application configuration.
        It is a resource class because the dagster framework requires
        it to be so.
    """
    app_config = app_config_resource.get_app_config()
    client = app_config.get_github_client()
    Session = get_session(app_config)
    db_service = DatabaseService(Session)
    ingestion_service = IngestionService(db_service, client)
    ingestion_service.fetch_and_persist_data()


@asset(deps=[persist_data])
async def persist_embeddings(app_config_resource: AppConfigResource) -> None:
    """
    Persist embeddings of the files in the database.
    This function depends on the `persist_data` asset to run first.

    Args:
        app_config_resource (AppConfigResource): The application configuration.
        It is a resource class because the dagster framework requires it to be so.
    """
    app_config = app_config_resource.get_app_config()
    openai_client = app_config.get_openai_client()
    Session = get_session(app_config)
    github_token = app_config.github_token
    auth_header = AuthHeader(Authorization="Authorization", token=github_token)
    persistance = EmbeddingPersistence(Session)
    embedder = OpenAIEmbedder(openai_client, app_config.embedding_model)
    embedding_service = EmbeddingService(
        persistance,
        embedder,
        auth_header,
        app_config.blacklisted_files,
        app_config.whitelisted_extensions,
    )

    await embedding_service.embed_and_persist_files()
