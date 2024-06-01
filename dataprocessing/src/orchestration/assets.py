from dagster import asset
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.processing import AppConfig, save_and_persist_data


engine = create_engine("sqlite://", echo=True)
Session = sessionmaker(engine)


@asset
def persist_data():
    client = AppConfig.from_env().get_github_client()
    return save_and_persist_data(Session, client)
