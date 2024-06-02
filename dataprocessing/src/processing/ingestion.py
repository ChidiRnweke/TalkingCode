from datetime import datetime
from github import Github
from dataclasses import dataclass
from github.ContentFile import ContentFile
from github.Repository import Repository
from src.processing.database import GithubFileModel
from src.processing.database import GitHubRepositoryModel
from src.processing.database import LanguagesModel
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import select
from typing import Self


def save_and_persist_data(session_maker: sessionmaker[Session], client: Github) -> None:
    process_repositories(client, session_maker)


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


def process_repositories(client: Github, session_maker: sessionmaker[Session]) -> None:
    for repo in client.get_user().get_repos():
        if repo.fork or repo.owner.login != client.get_user().login:
            continue
        data = repositories_by_user(repo)
        write_to_database(session_maker, data)


def repositories_by_user(
    repo: Repository,
) -> tuple[GitHubRepository, list[GitHubFile]]:

    repository = create_repository_object(repo)
    repo_contents = fetch_repository_contents(repo)
    files = [get_files_from_content(content) for content in repo_contents]
    return (repository, files)


def write_to_database(
    session_maker: sessionmaker[Session],
    data: tuple[GitHubRepository, list[GitHubFile]],
) -> None:
    with session_maker() as session:
        repo, files = data
        repo_model = repo.to_db_object()
        existing_languages = {
            lang.language: lang for lang in session.query(LanguagesModel).all()
        }
        existing_files_stmt = (
            select(GithubFileModel)
            .where(GithubFileModel.repository_name == repo.name)
            .where(GithubFileModel.repository_user == repo.user)
        )
        existing_files = {
            file.name: file for file in session.scalars(existing_files_stmt).all()
        }

        for file in files:
            if (
                file.name in existing_files
                and existing_files[file.name].last_modified >= file.last_modified
            ):
                continue
            elif file.name in existing_files:
                existing_file = existing_files[file.name]
                update_file_status(session, existing_file)

            process_file(repo, repo_model, existing_languages, file)

        session.add(repo_model)
        session.commit()


def update_file_status(session: Session, existing_file: GithubFileModel) -> None:
    existing_file.latest_version = False
    session.add(existing_file)


def process_file(
    repo: GitHubRepository,
    repo_model: GitHubRepositoryModel,
    existing_languages: dict[str, LanguagesModel],
    file: GitHubFile,
) -> None:
    file_model = file.to_db_object(repo)
    repo_model.files.append(file_model)
    for language in repo.languages:
        if language not in existing_languages:
            lang_model = LanguagesModel(language=language)
            existing_languages[language] = lang_model
            repo_model.languages.append(lang_model)
        else:
            repo_model.languages.append(existing_languages[language])


def fetch_repository_contents(repo: Repository) -> list[ContentFile]:
    repo_contents = []
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
    return repo_contents


def create_repository_object(repo: Repository) -> GitHubRepository:
    return GitHubRepository(
        name=repo.name,
        user=repo.owner.login,
        description=repo.description,
        languages=list(repo.get_languages().keys()),
        url=repo.html_url,
    )


def get_files_from_content(content: ContentFile) -> GitHubFile:
    return GitHubFile(
        name=content.name,
        content_url=content.download_url,
        last_modified=content.last_modified_datetime or datetime.now(),
        extension=content.name.split(".")[-1],
        path_in_project=content.path,
    )
