from logging import getLogger
from sqlite3 import Connection as SQLiteConnection

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, Engine, event

from .schema import Base, GithubFileModel, GitHubRepositoryModel

logger = getLogger("app_logger")


def run_migrations() -> None:
    logger.info("Running migrations...")
    try:
        alembic_cfg = Config()
        command.upgrade(alembic_cfg, "head")
        logger.info("Migrations complete.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise e


@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection: Connection, connection_record) -> None:
    if isinstance(dbapi_connection, SQLiteConnection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


__all__ = ["Base", "GitHubRepositoryModel", "GithubFileModel", "run_migrations"]
