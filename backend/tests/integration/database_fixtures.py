from datetime import datetime
import os
from backend.retrieval_augmented_generation.retrieve import (
    SQLRetrievalService,
)
import numpy as np
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from shared.database import (
    EmbeddedDocumentModel,
    GitHubRepositoryModel,
    GithubFileModel,
    run_migrations,
)
from logging import Logger
from typing import AsyncGenerator, Generator
import pytest_asyncio

logger = Logger("backend_logger")


@pytest.fixture(scope="session")
def database_session() -> Generator[async_sessionmaker[AsyncSession], None, None]:
    """
    Starts a Postgres container and creates a database session for testing.
    The scope of the fixture is session-wide, meaning that the container will be
    started once and the session will be created once for all tests. All tests
    are thus sharing the same database and in the current setup also share the
    same event loop.

    Yields:
        (Generator[async_sessionmaker[AsyncSession], None, None]): The database session generator.
    """
    with PostgresContainer(
        "pgvector/pgvector:0.7.0-pg16",
        username="postgres",
        password="postgres",
        dbname="chatGITpt",
        driver="asyncpg",
    ) as postgres:
        conn_str = postgres.get_connection_url()
        sync_conn_str = conn_str.replace("asyncpg", "psycopg2")
        os.environ["DATABASE_URL"] = sync_conn_str
        run_migrations("../shared/shared/migrations", logger)
        engine = create_async_engine(conn_str)
        Session = async_sessionmaker(engine, expire_on_commit=False)
        yield Session


@pytest_asyncio.fixture(scope="session")
async def add_fake_data(database_session: async_sessionmaker[AsyncSession]) -> None:
    """
    Adds fake data to the database for testing purposes. The data consists of a
    GitHub repository with two files, each with an embedded document.


    Args:
        database_session (async_sessionmaker[AsyncSession]): This is the fixture that
            provides the database session. It spins up a Postgres container and creates
            a session for testing.
    """
    repository = GitHubRepositoryModel(
        name="repo1",
        user="user1",
        url="http://repo1.com",
    )
    file1 = GithubFileModel(
        name="file1",
        content_url="http://file1.com",
        last_modified=datetime.now(),
        repository_name="repo1",
        repository_user="user1",
        file_extension="py",
        path_in_repo="path/to/file1.py",
        latest_version=True,
        is_embedded=False,
    )
    file2 = GithubFileModel(
        name="file2",
        content_url="http://file2.com",
        last_modified=datetime.now(),
        repository_name="repo1",
        repository_user="user1",
        file_extension="py",
        path_in_repo="path/to/file2.py",
        latest_version=True,
        is_embedded=False,
    )
    embedded_document1 = EmbeddedDocumentModel(
        document=file1,
        embedding=np.random.rand(3072).tolist(),
        input_token_count=100,
    )
    embedded_document2 = EmbeddedDocumentModel(
        document=file2,
        embedding=np.random.rand(3072).tolist(),
        input_token_count=100,
    )
    async with database_session() as session:
        file1.embedding.append(embedded_document1)
        file2.embedding.append(embedded_document2)
        repository.files.extend([file1, file2])
        session.add(repository)
        await session.commit()


@pytest_asyncio.fixture(scope="session")
async def retrieval_service(
    database_session: async_sessionmaker[AsyncSession],
    add_fake_data: None,
) -> AsyncGenerator[SQLRetrievalService, None]:
    """
    A fixture that provides a `SQLRetrievalService` instance for testing. It uses the
    database session to connect to the database and adds fake data to the database for
    testing purposes. It is a session-scoped fixture, meaning that the database session
    is created once for all tests and the fake data is added once for all tests.

    Args:
        database_session (async_sessionmaker[AsyncSession]): This is the fixture that
            provides the database session. It spins up a Postgres container and creates
            a session for testing.
        add_fake_data (None): This is the fixture that adds fake data to the database
            for testing purposes.

    Yields:
       ( AsyncGenerator[SQLRetrievalService, None]): The retrieval service instance.
    """

    async with database_session() as session:

        service = SQLRetrievalService(session)
        yield service
