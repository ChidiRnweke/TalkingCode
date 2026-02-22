"""Ingestion controller."""

from dataclasses import dataclass

import structlog

from talkingcode.domain.models import (
    IngestionRunInfo,
    RegisterRepoInput,
    RepositoryInfo,
    StartIngestionInput,
)
from talkingcode.errors import NotFoundError
from talkingcode.repository.repo_repository import RepoRepository
from talkingcode.services.ingestion.ingestion_service import IIngestionService

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True)
class IngestionController:
    """Controller for repo management and ingestion operations."""

    repo_repository: RepoRepository
    ingestion_service: IIngestionService

    async def register_repo(self, input_data: RegisterRepoInput) -> RepositoryInfo:
        """Register a new repository for tracking."""
        logger.info("Registering repo", owner=input_data.owner, name=input_data.name)
        return await self.repo_repository.register(input_data)

    async def list_repos(self) -> list[RepositoryInfo]:
        """List all tracked repositories."""
        return await self.repo_repository.list_all()

    async def get_repo(self, owner: str, name: str) -> RepositoryInfo:
        """Get a specific repository. Raises NotFoundError if not found."""
        repo = await self.repo_repository.get_by_owner_name(owner, name)
        if not repo:
            raise NotFoundError(resource=f"Repository {owner}/{name}")
        return repo

    async def start_ingestion(
        self,
        owner: str,
        name: str,
        git_ref: str | None = None,
    ) -> IngestionRunInfo:
        """Start an ingestion run for a repository."""
        repo = await self.repo_repository.get_by_owner_name(owner, name)
        if not repo:
            raise NotFoundError(resource=f"Repository {owner}/{name}")

        logger.info("Starting ingestion", repo=f"{owner}/{name}", ref=git_ref)
        return await self.ingestion_service.run_ingestion(
            StartIngestionInput(repository_id=repo.id, git_ref=git_ref)
        )

    async def list_ingestion_runs(self, owner: str, name: str) -> list[IngestionRunInfo]:
        """List ingestion runs for a repository."""
        repo = await self.repo_repository.get_by_owner_name(owner, name)
        if not repo:
            raise NotFoundError(resource=f"Repository {owner}/{name}")
        return await self.repo_repository.list_ingestion_runs(repo.id)
