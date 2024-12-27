import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from talkingcode.pipelines.github_client import GitHubClient
from talkingcode.pipelines.models import GitHubFile, GitHubRepository
from talkingcode.shared.database import (
    GithubFileModel,
    GitHubRepositoryModel,
    LanguagesModel,
)
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

logger = logging.getLogger("app_logger")


class Storage(Protocol):
    async def write_to_database(
        self, repo: GitHubRepository, files: list[GitHubFile]
    ) -> None: ...


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class MetadataIngestionService:
    """
    The `MetadataIngestionService` class is responsible for fetching data from the GitHub API and persisting it to the database.
    It handles the process of the initial fetch of the repositories, fetching the files for each repository, and saving the data to the database.
    Only metadata about the repositories is saved, not the actual file contents.

    It can be instantiated using the `from_config` class method, which reads the configuration from the environment variables or a secrets manager.

    Args:
        db (Storage): The database service to use for storing the fetched data.
        client (GitHubClient): The GitHub client to use for fetching data from the GitHub API.
    """

    db: Storage
    client: GitHubClient

    async def fetch_and_persist_metadata(self) -> None:
        """
        Fetches data from the GitHub API and persists it to the database.
        """
        await self._process_repositories()

    async def _process_repositories(self) -> None:
        user = await self.client.get_user()
        repos = await self.client.get_all_repositories()
        (user, repos) = await asyncio.gather(*[user, repos])
        repo_futures = [self._process_repository(user, repo) for repo in repos]
        await asyncio.gather(*repo_futures)

    async def _process_repository(self, user: str, repo: "GitHubRepository") -> None:
        if repo.fork or repo.owner != user:
            return None
        logger.info(f"Processing repository {repo.name}")
        files = await self.client.get_all_files(repo)
        logger.info(f"Found {len(files)} files in {repo.name}")
        await self.db.write_to_database(repo, files)


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class DatabaseService(Storage):
    session_maker: async_sessionmaker[AsyncSession]

    async def write_to_database(
        self,
        repo: GitHubRepository,
        files: list[GitHubFile],
    ) -> None:
        repo_model = repo.to_db_object()
        stmt = select(GitHubRepositoryModel).filter_by(name=repo.name, user=repo.user)
        async with self.session_maker() as session:
            existing_languages = await self._get_existing_languages(session)

            existing_repo = (await session.scalars(stmt)).first()

            if existing_repo:
                existing_repo.description = repo_model.description
                existing_repo.url = repo_model.url

                existing_files = await self._get_existing_files(session, repo)
                for file in files:
                    self._process_if_new(
                        file,
                        repo,
                        existing_repo,
                        existing_languages,
                        existing_files,
                    )

                for language in repo.languages:
                    self._add_language_to_repo(
                        existing_repo, existing_languages, language
                    )
            else:
                session.add(repo_model)
                for file in files:
                    file_model = file.to_db_object(repo)
                    repo_model.files.append(file_model)
                for language in repo.languages:
                    self._add_language_to_repo(repo_model, existing_languages, language)

            await session.commit()
            logger.debug(f"Saved {repo.name} to the database")

    def _process_if_new(
        self,
        file: GitHubFile,
        repo: GitHubRepository,
        repo_model: GitHubRepositoryModel,
        existing_languages: dict[str, LanguagesModel],
        existing_files: dict[str, GithubFileModel],
    ) -> None:
        already_exists = file.path_in_project in existing_files

        if already_exists:
            needs_update = existing_files[file.path_in_project].sha != file.sha
            if needs_update:
                existing_file = existing_files[file.path_in_project]
                existing_file.latest_version = False
                self._add_file_to_repository(repo, repo_model, existing_languages, file)
            else:
                return None
        else:
            self._add_file_to_repository(repo, repo_model, existing_languages, file)

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

    async def _get_existing_languages(
        self, session: AsyncSession
    ) -> dict[str, LanguagesModel]:
        stmt = select(LanguagesModel)
        languages = (await session.scalars(stmt)).all()
        return {lang.language: lang for lang in languages}

    def _add_file_to_repository(
        self,
        repo: GitHubRepository,
        repo_model: GitHubRepositoryModel,
        existing_languages: dict[str, LanguagesModel],
        file: GitHubFile,
    ) -> None:
        file_model = file.to_db_object(repo)
        repo_model.files.append(file_model)
        for language in repo.languages:
            self._add_language_to_repo(repo_model, existing_languages, language)

    def _add_language_to_repo(
        self,
        repo_model: GitHubRepositoryModel,
        existing_languages: dict[str, LanguagesModel],
        language: str,
    ) -> None:
        if language not in existing_languages:
            lang_model = LanguagesModel(language=language)
            existing_languages[language] = lang_model
            repo_model.languages.append(lang_model)
        else:
            if existing_languages[language] not in repo_model.languages:
                repo_model.languages.append(existing_languages[language])
