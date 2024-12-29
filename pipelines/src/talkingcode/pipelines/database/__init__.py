from logging import getLogger
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import Connection, Engine, event

from .schema import Base, GithubFileModel, GitHubRepositoryModel, LanguagesModel

logger = getLogger("app_logger")


@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection: Connection, connection_record) -> None:
    if isinstance(dbapi_connection, SQLiteConnection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA read_uncommitted=1")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=OFF")
        cursor.close()


__all__ = ["Base", "GitHubRepositoryModel", "GithubFileModel", "LanguagesModel"]
