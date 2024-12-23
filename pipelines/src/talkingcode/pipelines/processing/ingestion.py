from dataclasses import dataclass

from pipelines.processing.models import AuthHeader, GitHubFile, GitHubRepository

from shared.database import GithubFileModel
from shared.database import GitHubRepositoryModel
from shared.database import LanguagesModel
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select
from typing import Protocol
import logging
import asyncio
import aiohttp


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

    async def get_all_repositories(self) -> list["GitHubRepository"]:
        header = self.auth_header.to_dict()
        path = "https://api.github.com/user/repos"
        async with aiohttp.ClientSession() as session:
            async with session.get(path, headers=header) as response:
                repos = await response.json()
                return [
                    GitHubRepository(
                        name=repo["name"],
                        user=repo["owner"]["login"],
                        description=repo.get("description", ""),
                        languages=[],
                        url=repo["html_url"],
                        owner=repo["owner"]["login"],
                        fork=repo["fork"],
                        default_branch=repo["default_branch"],
                    )
                    for repo in repos
                ]

    async def get_all_files(self, repo: GitHubRepository) -> list[GitHubFile]:
        header = self.auth_header.to_dict()
        path = f"https://api.github.com/repos/{repo.user}/{repo.name}/git/trees/{repo.default_branch}?recursive=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(path, headers=header) as response:
                files = await response.json()
                file_paths = [
                    file["path"] for file in files["tree"] if file["type"] == "blob"
                ]
            links = []
            for file_path in file_paths:
                content_path = f"https://api.github.com/repos/{repo.user}/{repo.name}/contents/{file_path}"
                async with session.get(content_path, headers=header) as response:
                    file = response.json()
                    links.append(file)
            responses = await asyncio.gather(*links)

            return [
                GitHubFile(
                    name=file["name"],
                    content_url=file["download_url"],
                    last_modified=file["last_modified"],
                    extension=file["name"].split(".")[-1],
                    path_in_project=file["path"],
                )
                for file in responses
            ]

    async def get_user(self) -> str:
        header = self.auth_header.to_dict()
        path = "https://api.github.com/user"
        async with aiohttp.ClientSession() as session:
            async with session.get(path, headers=header) as response:
                return (await response.json())["login"]


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
        repo_futures = [self.process_repository(user, repo) for repo in repos]
        await asyncio.gather(*repo_futures)

    async def process_repository(self, user: str, repo: "GitHubRepository") -> None:
        if repo.fork or repo.owner != user:
            return None
        logger.info(f"Processing repository {repo.name}")
        files = await self.client.get_all_files(repo)
        logger.info(f"Found {len(files)} files in {repo.name}")
        await self.db.write_to_database(repo, files)


@dataclass(frozen=True)
class DatabaseService(Storage):
    session_maker: sessionmaker[Session]

    async def write_to_database(
        self,
        repo: GitHubRepository,
        files: list[GitHubFile],
    ) -> None:
        repo_model = repo.to_db_object()

        with self.session_maker() as session:
            existing_languages = self._get_existing_languages(session)
            existing_repo = (
                session.query(GitHubRepositoryModel)
                .filter_by(name=repo.name, user=repo.user)
                .first()
            )

            if existing_repo:
                existing_repo.description = repo_model.description
                existing_repo.url = repo_model.url

                existing_files = self._get_existing_files(session, repo)
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

            session.commit()
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
            needs_update = (
                existing_files[file.path_in_project].last_modified.timestamp()
                < file.last_modified.timestamp()
            )
            if needs_update:
                existing_file = existing_files[file.path_in_project]
                existing_file.latest_version = False
                self._add_file_to_repository(repo, repo_model, existing_languages, file)
            else:
                return None
        else:
            self._add_file_to_repository(repo, repo_model, existing_languages, file)

    def _get_existing_repositories(
        self,
    ) -> dict[str, GitHubRepositoryModel]:
        with self.session_maker() as session:
            return {
                repo.name: repo for repo in session.query(GitHubRepositoryModel).all()
            }

    def _get_existing_files(
        self, session: Session, repo: GitHubRepository
    ) -> dict[str, GithubFileModel]:
        existing_files_stmt = (
            select(GithubFileModel)
            .where(GithubFileModel.repository_name == repo.name)
            .where(GithubFileModel.repository_user == repo.user)
        )
        return {
            file.path_in_repo: file
            for file in session.scalars(existing_files_stmt).all()
        }

    def _get_existing_languages(self, session: Session) -> dict[str, LanguagesModel]:
        return {lang.language: lang for lang in session.query(LanguagesModel).all()}

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
