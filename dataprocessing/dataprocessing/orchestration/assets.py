from dagster import asset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dataprocessing.orchestration.resources import AppConfigResource
from dataprocessing.processing import (
    AppConfig,
    IngestionService,
    DatabaseService,
    AuthHeader,
    EmbeddingService,
    TextEmbedder,
    EmbeddingPersistance,
)


def get_session(app: AppConfig) -> sessionmaker[Session]:
    engine = create_engine(app.db_connection_string, echo=True)
    Session = sessionmaker(engine)
    return Session


@asset
def persist_data(app_config_resource: AppConfigResource) -> None:
    app_config = app_config_resource.get_app_config()
    client = app_config.get_github_client()
    Session = get_session(app_config)
    db_service = DatabaseService(Session)
    ingestion_service = IngestionService(db_service, client)
    ingestion_service.fetch_and_persist_data()


@asset(deps=[persist_data])
async def persist_embeddings(app_config_resource: AppConfigResource) -> None:
    app_config = app_config_resource.get_app_config()
    openai_client = app_config.get_openai_client()
    Session = get_session(app_config)
    github_token = app_config.github_token
    auth_header = AuthHeader(Authorization="Authorization", token=github_token)
    persistance = EmbeddingPersistance(Session)
    embedder = TextEmbedder(openai_client, app_config.embedding_model)
    embedding_service = EmbeddingService(
        persistance,
        embedder,
        auth_header,
        app_config.blacklisted_files,
        app_config.whitelisted_extensions,
    )

    await embedding_service.embed_and_persist_files()
