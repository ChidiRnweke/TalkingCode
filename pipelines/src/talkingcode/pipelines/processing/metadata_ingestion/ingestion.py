import asyncio
from dataclasses import dataclass
from typing import ClassVar

import structlog

from talkingcode.pipelines.github_client import GitHubClient
from talkingcode.pipelines.models import GitHubRepository
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

from .storage import MetadataStorage

logger = structlog.getLogger("talkingcode")


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
        sync_mode (bool): Whether to write to the database in synchronous mode. Defaults to False.
    """

    db: MetadataStorage
    client: GitHubClient
    sync_mode: bool = False
    _db_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    async def fetch_and_persist_metadata(self) -> None:
        """
        Fetches metadata from the GitHub API and persists it to the database.
        """
        await self._process_repositories()

    async def _process_repositories(self) -> None:
        user = self.client.get_user()
        _repos = self.client.get_all_repositories()
        (user, _repos) = await asyncio.gather(*[user, _repos])
        _repos = [self._process_repository(user, repo) for repo in _repos]
        await asyncio.gather(*_repos)

    async def _process_repository(self, user: str, repo: "GitHubRepository") -> None:
        if repo.fork or repo.owner != user:
            return None
        logger.info(f"Processing repository {repo.name}")
        files = await self.client.get_all_files(repo)
        logger.debug(f"Found {len(files)} files in {repo.name}")
        if self.sync_mode:
            async with MetadataIngestionService._db_lock:
                await self.db.write_to_database(repo, files)
        else:
            await self.db.write_to_database(repo, files)
