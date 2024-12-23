from dataclasses import dataclass
from typing import Self

from talkingcode.shared.database import GitHubRepositoryModel, GithubFileModel


@dataclass(frozen=True, slots=True)
class AuthHeader:
    """
    Small dataclass to store the authorization header for the API requests.
    Necessary for the requests to the GitHub API.

    Args:
        Authorization (str): The name of the authorization header. (for example `Authorization`)
        token (str): The token to be used for authorization. This is the GitHub token, in this case
            you need to request a classic GitHub token.
    """

    Authorization: str
    token: str

    def to_dict(self) -> dict[str, str]:
        """Returns the authorization header as a dictionary.
        The dictionary is used to pass the authorization header to the aiohttp library. This is necessary
        for the requests to the GitHub API.

        Returns:
            dict[str, str]: The authorization header as a dictionary.
        """
        return {"Authorization": f"Bearer {self.token}"}


@dataclass(frozen=True, slots=True)
class GitHubRepository:
    name: str
    user: str
    description: str
    languages: list[str]
    url: str
    owner: str
    fork: bool
    default_branch: str

    def to_db_object(self) -> "GitHubRepositoryModel":
        return GitHubRepositoryModel(
            name=self.name,
            user=self.user,
            description=self.description,
            url=self.url,
            languages=[],
        )


@dataclass(frozen=True, slots=True)
class GitHubFile:
    name: str
    content_url: str
    sha: str
    extension: str
    path_in_project: str

    @classmethod
    def from_db_object(cls, file: GithubFileModel) -> Self:
        return cls(
            name=file.name,
            content_url=file.content_url,
            sha=file.sha,
            extension=file.file_extension,
            path_in_project=file.path_in_repo,
        )

    def to_db_object(self, repository: GitHubRepository) -> "GithubFileModel":
        return GithubFileModel(
            name=self.name,
            content_url=self.content_url,
            sha=self.sha,
            repository_name=repository.name,
            repository_user=repository.user,
            file_extension=self.extension,
            path_in_repo=self.path_in_project,
            latest_version=True,
            is_embedded=False,
        )


@dataclass(frozen=True, slots=True)
class FileMetadata:
    """
    This class is used to store metadata about the files that are to be embedded.

    Args:
        repository_name (str): The name of the repository that the file belongs to.
        document_id (int): The id of the document in the database.
        file (GitHubFile): The file object that contains metadata about the file.
    """

    repository_name: str
    document_id: int
    file: GitHubFile

    @classmethod
    def from_db_object(cls, file: GithubFileModel) -> Self:
        """
        Creates a FileMetadata object from a GithubFileModel object.
        The point is to convert the database object into a domain object.


        Args:
            file (GithubFileModel): The database object to convert.

        Returns:
            Self: The domain object.
        """
        return cls(
            repository_name=file.repository_name,
            document_id=file.id,
            file=GitHubFile.from_db_object(file),
        )
