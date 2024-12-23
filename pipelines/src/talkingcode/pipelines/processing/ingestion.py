import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.github_models.file_content import ContentTree
from talkingcode.pipelines.github_models.files import GitTree
from talkingcode.pipelines.github_models.languages import Languages
from talkingcode.pipelines.github_models.repositories import (
    RepositoriesResponse,
    Repository,
)
from talkingcode.pipelines.github_models.user import User
from talkingcode.shared.database import (
    GithubFileModel,
    GitHubRepositoryModel,
    LanguagesModel,
)
from talkingcode.shared.telemetry import log_execution_time

from .models import AuthHeader, GitHubFile, GitHubRepository

logger = logging.getLogger("app_logger")


class GitHubClient(Protocol):
    async def get_all_repositories(self) -> list[GitHubRepository]: ...

    async def get_all_files(self, repo: GitHubRepository) -> list[GitHubFile]: ...

    async def get_user(self) -> str: ...


class Storage(Protocol):
    async def write_to_database(
        self, repo: GitHubRepository, files: list[GitHubFile]
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class GithubHTTPClient(GitHubClient):
    auth_header: AuthHeader

    @log_execution_time
    async def get_all_repositories(self) -> list["GitHubRepository"]:
        header = self.auth_header.to_dict()
        path = "https://api.github.com/user/repos"
        language_result = []
        async with AsyncClient() as client:
            response = await client.get(path, headers=header)
            _repos = response.json()
            repos = RepositoriesResponse(root=_repos)
        for repo in repos.root:
            languages_task = self.language_from_repo(repo)
            language_result.append(languages_task)
        languages = await asyncio.gather(*language_result)
        return [
            GitHubRepository(
                name=repo.name,
                user=repo.owner.login,
                description=repo.description or "",
                languages=langs,
                url=repo.html_url,
                owner=repo.owner.login,
                fork=repo.fork,
                default_branch=repo.default_branch,
            )
            for repo, langs in zip(repos.root, languages)
        ]

    @log_execution_time
    async def language_from_repo(self, repo: Repository) -> list[str]:
        header = self.auth_header.to_dict()
        path = repo.languages_url
        async with AsyncClient() as client:
            response = await client.get(path, headers=header)
            langs_and_usage = Languages(root=response.json())
            if langs := langs_and_usage.root:
                return list(langs.keys())
            else:
                return []

    @log_execution_time
    async def get_all_files(self, repo: GitHubRepository) -> list[GitHubFile]:
        header = self.auth_header.to_dict()
        path = f"https://api.github.com/repos/{repo.user}/{repo.name}/git/trees/{repo.default_branch}?recursive=1"
        async with AsyncClient() as client:
            response = await client.get(path, headers=header)
            files = GitTree(**response.json())
            file_paths = [file.path for file in files.tree if file.type == "blob"]
            links = []
            for file_path in file_paths:
                content_path = f"https://api.github.com/repos/{repo.user}/{repo.name}/contents/{file_path}"
                file = client.get(content_path, headers=header)
                links.append(file)
            responses = await asyncio.gather(*links)
            responses = [ContentTree(**response.json()) for response in responses]

        return [
            GitHubFile(
                name=file.name,
                content_url=file.download_url or "",
                sha=file.sha,
                extension=file.name.split(".")[-1],
                path_in_project=file.path,
            )
            for file in responses
        ]

    @log_execution_time
    async def get_user(self) -> str:
        header = self.auth_header.to_dict()
        path = "https://api.github.com/user"
        async with AsyncClient() as client:
            response = await client.get(path, headers=header)
            return User(**response.json()).root.login

    @classmethod
    def from_config(cls, config: IngestionConfig) -> "GithubHTTPClient":
        header = AuthHeader(Authorization="Authorization", token=config.github_token)
        return cls(header)


@dataclass(frozen=True)
class IngestionService:
    db: Storage
    client: GitHubClient

    async def fetch_and_persist_data(self) -> None:
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

    @classmethod
    def from_config(cls, config: IngestionConfig) -> "IngestionService":
        db = DatabaseService.from_config(config)
        client = GithubHTTPClient.from_config(config)
        return cls(db=db, client=client)


@dataclass(frozen=True)
class DatabaseService(Storage):
    session_maker: async_sessionmaker[AsyncSession]

    @log_execution_time
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

    @classmethod
    def from_config(cls, config: IngestionConfig) -> "DatabaseService":
        engine = create_async_engine(config.db_connection_string)
        Session = async_sessionmaker(engine, expire_on_commit=False)
        return cls(session_maker=Session)
