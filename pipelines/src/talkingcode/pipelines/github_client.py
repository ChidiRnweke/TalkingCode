import asyncio
from dataclasses import dataclass
from logging import getLogger
from typing import ClassVar, Protocol

from httpx import AsyncClient
from tenacity import retry, stop_after_attempt, wait_exponential

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.github_models.file_content import ContentTree
from talkingcode.pipelines.github_models.files import GitTree
from talkingcode.pipelines.github_models.languages import Languages
from talkingcode.pipelines.github_models.repositories import (
    RepositoriesResponse,
    Repository,
)
from talkingcode.pipelines.github_models.user import User
from talkingcode.pipelines.models import (
    AuthHeader,
    GitHubFile,
    GitHubRepository,
)
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

logger = getLogger("app_logger")


class GitHubClient(Protocol):
    async def get_all_repositories(self) -> list[GitHubRepository]: ...

    async def get_file_content(self, file: GitHubFile) -> str: ...

    async def get_all_files(self, repo: GitHubRepository) -> list[GitHubFile]: ...

    async def get_user(self) -> str: ...


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class GithubHTTPClient(GitHubClient):
    """
    The GithubHTTPClient class is responsible for fetching data from the GitHub API.

    Args:
        Args:
        auth_header (AuthHeader): The authentication header to use for making requests to the GitHub API.
    """

    auth_header: AuthHeader
    _semaphore: ClassVar[asyncio.Semaphore] = asyncio.Semaphore(30)

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    async def get_all_repositories(self) -> list[GitHubRepository]:
        """
        Fetches all repositories for the authenticated user.

        Returns:
            list[GitHubRepository]: A list of GitHubRepository objects representing the repositories.
        """
        header = self.auth_header.to_dict()
        path = "https://api.github.com/user/repos"
        language_result = []
        async with GithubHTTPClient._semaphore:
            async with AsyncClient(timeout=500) as client:
                response = await client.get(path, headers=header)
            _repos = response.json()
            repos = RepositoriesResponse(root=_repos)
        logger.info(
            f"Found {len(repos.root)} repositories for user {await self.get_user()}"
        )
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

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    async def get_file_content(self, file: GitHubFile) -> str:
        header = self.auth_header.to_dict()
        path = file.content_url
        async with GithubHTTPClient._semaphore:
            async with AsyncClient(timeout=500) as client:
                response = await client.get(path, headers=header)
            return response.text

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    async def language_from_repo(self, repo: Repository) -> list[str]:
        header = self.auth_header.to_dict()
        path = repo.languages_url
        async with GithubHTTPClient._semaphore:
            async with AsyncClient(timeout=500) as client:
                response = await client.get(path, headers=header)
            langs_and_usage = Languages(root=response.json())
            if langs := langs_and_usage.root:
                return list(langs.keys())
            else:
                return []

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    async def get_all_files(self, repo: GitHubRepository) -> list[GitHubFile]:
        logger.info(f"Fetching files for {repo.name}")
        header = self.auth_header.to_dict()
        path = f"https://api.github.com/repos/{repo.user}/{repo.name}/git/trees/{repo.default_branch}?recursive=1"

        async with GithubHTTPClient._semaphore:
            async with AsyncClient(timeout=500) as client:
                response = await client.get(path, headers=header)
                files = GitTree(**response.json())
                file_paths = [file.path for file in files.tree if file.type == "blob"]
                links = []
                for file_path in file_paths:
                    content_path = f"https://api.github.com/repos/{repo.user}/{repo.name}/contents/{file_path}"
                    async with GithubHTTPClient._semaphore:
                        file = client.get(content_path, headers=header)
                        links.append(file)
                responses = await asyncio.gather(*links)
                responses = [ContentTree(**response.json()) for response in responses]
                logger.debug(f"Found {len(responses)} files for {repo.name}")

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

    @retry(
        stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    async def get_user(self) -> str:
        header = self.auth_header.to_dict()
        path = "https://api.github.com/user"
        async with GithubHTTPClient._semaphore:
            async with AsyncClient(timeout=500) as client:
                response = await client.get(path, headers=header)
            return User(**response.json()).root.login

    @classmethod
    def from_config(cls, config: IngestionConfig) -> "GithubHTTPClient":
        """
        Factory method to create an instance of the GithubHTTPClient class from a configuration object.


        Args:
            config (IngestionConfig): The configuration object to use for creating the client.

        Returns:
            GithubHTTPClient: An instance of the GithubHTTPClient class.
        """
        header = AuthHeader(Authorization="Authorization", token=config.github_token)
        return cls(header)
