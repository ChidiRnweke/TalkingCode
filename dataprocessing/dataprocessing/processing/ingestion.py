from datetime import datetime
from github import Github
from dataclasses import dataclass
from github.ContentFile import ContentFile
from github.Repository import Repository
from shared.database import GithubFileModel
from shared.database import GitHubRepositoryModel
from shared.database import LanguagesModel
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select
from typing import Self
import logging

logger = logging.getLogger("app_logger")


@dataclass(frozen=True)
class IngestionService:
    db: "DatabaseService"
    client: Github

    def fetch_and_persist_data(self) -> None:
        self._process_repositories()

    def _process_repositories(self) -> None:
        existing_repos = self.db._get_existing_repositories()
        for repo in self.client.get_user().get_repos():
            if repo.fork or repo.owner.login != self.client.get_user().login:
                continue
            logger.info(f"Processing repository {repo.name}")
            repo_with_files = self._process_single_repository(repo)
            logger.info(
                f"Found {len(repo_with_files[1])} files in {repo_with_files[0].name}"
            )

            self.db.write_to_database(repo_with_files, existing_repos)

    def _process_single_repository(
        self, repo: Repository
    ) -> tuple["GitHubRepository", list["GitHubFile"]]:

        repository = GitHubRepository.from_repository_object(repo)
        files = GitHubFile.from_repository_object(repo)
        return (repository, files)


@dataclass(frozen=True)
class GitHubRepository:
    name: str
    user: str
    description: str
    languages: list[str]
    url: str

    def to_db_object(self) -> "GitHubRepositoryModel":

        return GitHubRepositoryModel(
            name=self.name,
            user=self.user,
            description=self.description,
            url=self.url,
            languages=[],
        )

    @classmethod
    def from_repository_object(cls, repo: Repository) -> "GitHubRepository":
        return cls(
            name=repo.name,
            user=repo.owner.login,
            description=repo.description,
            languages=list(repo.get_languages().keys()),
            url=repo.html_url,
        )


@dataclass(frozen=True)
class GitHubFile:
    name: str
    content_url: str
    last_modified: datetime
    extension: str
    path_in_project: str

    @classmethod
    def from_db_object(cls, file: GithubFileModel) -> Self:
        return cls(
            name=file.name,
            content_url=file.content_url,
            last_modified=file.last_modified,
            extension=file.file_extension,
            path_in_project=file.path_in_repo,
        )

    @classmethod
    def from_content_file(cls, content: ContentFile) -> "GitHubFile":
        return cls(
            name=content.name,
            content_url=content.download_url,
            last_modified=content.last_modified_datetime or datetime.now(),
            extension=content.name.split(".")[-1],
            path_in_project=content.path,
        )

    @classmethod
    def from_repository_object(cls, repo: Repository) -> list["GitHubFile"]:
        repo_contents: list[ContentFile] = []
        contents = repo.get_contents("")
        contents = contents if isinstance(contents, list) else [contents]

        while contents:
            content = contents.pop(0)
            if content.type == "dir":
                children = repo.get_contents(content.path)
                children = children if isinstance(children, list) else [children]
                contents.extend(children)
            else:
                repo_contents.append(content)
        return [cls.from_content_file(content) for content in repo_contents]

    def to_db_object(self, repository: GitHubRepository) -> "GithubFileModel":
        return GithubFileModel(
            name=self.name,
            content_url=self.content_url,
            last_modified=self.last_modified,
            repository_name=repository.name,
            repository_user=repository.user,
            file_extension=self.extension,
            path_in_repo=self.path_in_project,
            latest_version=True,
            is_embedded=False,
        )


@dataclass(frozen=True)
class DatabaseService:
    session_maker: sessionmaker[Session]

    def write_to_database(
        self,
        data: tuple[GitHubRepository, list[GitHubFile]],
        existing_repos: dict[str, GitHubRepositoryModel],
    ) -> None:
        repo, files = data
        repo_model = repo.to_db_object()

        with self.session_maker() as session:

            existing_languages = self._get_existing_languages(session)
            existing_files = self._get_existing_files(session, repo)
            for file in files:
                self._process_if_new(
                    file,
                    repo,
                    repo_model,
                    existing_languages,
                    existing_files,
                )
            if repo.name not in existing_repos:
                session.add(repo_model)
            else:
                session.merge(repo_model)

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
            repo_model.languages.append(existing_languages[language])
