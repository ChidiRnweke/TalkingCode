import logging
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from talkingcode.pipelines.database import (
    GithubFileModel,
    GitHubRepositoryModel,
)
from talkingcode.pipelines.models import GitHubFile, GitHubRepository
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

logger = logging.getLogger("app_logger")


class MetadataStorage(Protocol):
    async def write_to_database(
        self, repo: GitHubRepository, files: list[GitHubFile]
    ) -> None: ...


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class DatabaseService(MetadataStorage):
    session_maker: async_sessionmaker[AsyncSession]

    async def write_to_database(
        self,
        repo: GitHubRepository,
        files: list[GitHubFile],
    ) -> None:
        repo_model = repo.to_db_object()
        stmt = select(GitHubRepositoryModel).filter_by(name=repo.name, user=repo.user)
        async with self.session_maker() as session:
            with session.no_autoflush:
                existing_repo = (await session.scalars(stmt)).first()

                if existing_repo:
                    existing_repo.description = repo_model.description
                    existing_repo.url = repo_model.url

                    existing_files = await self._get_existing_files(session, repo)
                    for file in files:
                        await self._process_if_new(
                            file,
                            repo,
                            existing_repo,
                            existing_files,
                        )

                else:
                    session.add(repo_model)
                    for file in files:
                        file_model = file.to_db_object(repo)
                        repo_model.files.append(file_model)

                await session.flush()
                await session.commit()
                logger.info(f"Saved {repo.name} to the database")

    async def _process_if_new(
        self,
        file: GitHubFile,
        repo: GitHubRepository,
        repo_model: GitHubRepositoryModel,
        existing_files: dict[str, GithubFileModel],
    ) -> None:
        already_exists = file.path_in_project in existing_files

        if already_exists:
            needs_update = existing_files[file.path_in_project].sha != file.sha
            if needs_update:
                existing_file = existing_files[file.path_in_project]
                existing_file.latest_version = False
                await self._add_file_to_repository(repo, repo_model, file)
            else:
                return None
        else:
            await self._add_file_to_repository(repo, repo_model, file)

    async def _get_existing_repositories(
        self,
    ) -> dict[str, GitHubRepositoryModel]:
        stmt = select(GitHubRepositoryModel)
        async with self.session_maker() as session:
            existing_repos = (await session.scalars(stmt)).all()
        return {repo.name: repo for repo in existing_repos}

    async def _get_existing_files(
        self, session: AsyncSession, repo: GitHubRepository
    ) -> dict[str, GithubFileModel]:
        existing_files_stmt = (
            select(GithubFileModel)
            .where(GithubFileModel.repository_name == repo.name)
            .where(GithubFileModel.repository_user == repo.user)
        )
        existing_files = await session.scalars(existing_files_stmt)
        return {file.path_in_repo: file for file in existing_files.all()}

    async def _add_file_to_repository(
        self,
        repo: GitHubRepository,
        repo_model: GitHubRepositoryModel,
        file: GitHubFile,
    ) -> None:
        file_model = file.to_db_object(repo)
        repo_model.files.append(file_model)
