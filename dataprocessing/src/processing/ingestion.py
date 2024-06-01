from datetime import datetime
from github import Github
from dataclasses import dataclass
from github.ContentFile import ContentFile
from github.Repository import Repository
from src.processing.database import GithubFileModel
from src.processing.database import GitHubRepositoryModel
from src.processing.database import LanguagesModel
from sqlalchemy.orm import sessionmaker, Session


def save_and_persist_data(session_maker: sessionmaker[Session], client: Github) -> None:
    data = repositories_by_user(client)
    write_to_database(session_maker, data)


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


def repositories_by_user(
    client: Github,
) -> list[tuple[GitHubRepository, list[GitHubFile]]]:
    user_repos = client.get_user().get_repos()

    result = []
    for repo in user_repos:
        repository = create_repository_object(repo)
        repo_contents = fetch_repository_contents(repo)
        files = [get_files_from_content(content) for content in repo_contents]
        result.append((repository, files))
    return result


def write_to_database(
    session_maker: sessionmaker[Session],
    data: list[tuple[GitHubRepository, list[GitHubFile]]],
) -> None:
    with session_maker() as session:
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
