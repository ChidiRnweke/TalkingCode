from datetime import datetime
from github import Github
from dataclasses import dataclass
import os
from github import Auth
from github.ContentFile import ContentFile
from github.Repository import Repository
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Table


@dataclass(frozen=True)
class AppConfig:
    api_key: str

    @staticmethod
    def from_env():
        api_key = os.getenv("GITHUB_API_KEY")
        if api_key is None:
            raise ValueError("API_KEY is not set and is required to run the pipeline.")
        return AppConfig(api_key=api_key)

    def get_github_client(self) -> Github:
        auth = Auth.Token(self.api_key)
        return Github(auth=auth)


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
            languages=set(),
        )


@dataclass(frozen=True)
class GitHubFile:
    name: str
    content_url: str
    last_modified: datetime

    def to_db_object(self, repository: GitHubRepository) -> "GithubFileModel":
        return GithubFileModel(
            name=self.name,
            content_url=self.content_url,
            last_modified=self.last_modified,
            repository_name=repository.name,
            repository_user=repository.user,
        )


class Base(DeclarativeBase):
    pass


class LanguagesModel(Base):
    __tablename__ = "github_languages"

    language: Mapped[str] = mapped_column(String(255), primary_key=True)


languages_repository_bridge = Table(
    "association_table",
    Base.metadata,
    Column("language_name", ForeignKey("github_languages.name")),
    Column("repository_name", ForeignKey("github_repositories.name")),
    Column("repository_user", ForeignKey("github_repositories.user")),
)


class GitHubRepositoryModel(Base):
    __tablename__ = "github_repositories"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    user: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[str] = mapped_column(String(255))

    url: Mapped[str] = mapped_column(String(255))

    files: Mapped[list["GithubFileModel"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    languages: Mapped[set[LanguagesModel]] = relationship(
        secondary=languages_repository_bridge
    )


class GithubFileModel(Base):
    __tablename__ = "github_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    content_url: Mapped[str] = mapped_column(String(255))
    last_modified: Mapped[DateTime]
    repository_name: Mapped[str] = mapped_column(ForeignKey("github_repositories.name"))
    repository_user: Mapped[str] = mapped_column(ForeignKey("github_repositories.user"))

    repository: Mapped[GitHubRepositoryModel] = relationship(back_populates="files")


def repositories_by_user(
    config: AppConfig,
) -> list[tuple[GitHubRepository, list[GitHubFile]]]:
    client = config.get_github_client()
    user_repos = client.get_user().get_repos()

    result = []
    for repo in user_repos:
        repository = create_repository_object(repo)
        repo_contents = fetch_repository_contents(repo)
        files = [get_files_from_content(content) for content in repo_contents]
        result.append((repository, files))
    return result


def write_to_database(
    session: Session, data: list[tuple[GitHubRepository, list[GitHubFile]]]
) -> None:
    for repo, files in data:
        repo_model = repo.to_db_object()
        for file in files:
            file_model = file.to_db_object(repo)
            repo_model.files.append(file_model)
            existing_languages = {
                lang.language for lang in session.query(LanguagesModel).all()
            }
            for language in repo.languages:
                if language not in existing_languages:
                    repo_model.languages.add(LanguagesModel(language=language))
                else:
                    existing_language = (
                        session.query(LanguagesModel)
                        .filter_by(language=language)
                        .first()
                    )
                    repo_model.languages.add(existing_language)  # type: ignore

        session.add(repo_model)
    session.commit()


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
    )
