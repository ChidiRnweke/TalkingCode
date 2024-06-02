from dagster import asset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.processing import AppConfig, save_and_persist_data


@asset
def persist_data():
    config = AppConfig.from_env()
    client = config.get_github_client()
    engine = create_engine(config.db_connection_string, echo=True)
    Session = sessionmaker(engine)
    return save_and_persist_data(Session, client)
