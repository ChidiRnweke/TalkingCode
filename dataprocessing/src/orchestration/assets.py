from dagster import asset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.orchestration.resources import AppConfigResource
from src.processing import save_and_persist_data, embed_and_persist_files
from openai import AsyncOpenAI


@asset
def persist_data(app_config_resource: AppConfigResource) -> None:
    app_config = app_config_resource.get_app_config()
    client = app_config.get_github_client()
    engine = create_engine(app_config.db_connection_string, echo=True)
    Session = sessionmaker(engine)
    save_and_persist_data(Session, client)


@asset(deps=[persist_data])
async def persist_embeddings(app_config_resource: AppConfigResource) -> None:
    app_config = app_config_resource.get_app_config()
    engine = create_engine(app_config.db_connection_string, echo=True)
    Session = sessionmaker(engine)
    openai_client = AsyncOpenAI(api_key=app_config.openai_api_key)
    github_client = app_config.get_github_client()
    await embed_and_persist_files(
        Session,
        app_config.whitelisted_extensions,
        openai_client,
        github_client,
        app_config.embedding_model,
        app_config.embedding_disk_path,
    )
