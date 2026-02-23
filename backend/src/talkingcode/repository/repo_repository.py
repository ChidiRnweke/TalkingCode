"""Repository management repository."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.domain.models import IngestionRunInfo, RegisterRepoInput, RepositoryInfo
from talkingcode.enums import IngestionStatus
from talkingcode.models.orm import IngestionRun, Repository

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True)
class RepoRepository:
    """Repository for repo management operations."""

    session: AsyncSession

    async def register(self, input_data: RegisterRepoInput) -> RepositoryInfo:
        """Register a new repo. Upsert on (provider, owner, name)."""
        stmt = (
            insert(Repository)
            .values(
                id=uuid4(),
                provider=input_data.provider,
                owner=input_data.owner,
                name=input_data.name,
                default_branch=input_data.default_branch,
                created_at=datetime.utcnow(),
            )
            .on_conflict_do_update(
                constraint="uq_repo_provider_owner_name",
                set_={
                    "default_branch": input_data.default_branch,
                },
            )
        )

        await self.session.execute(stmt)
        await self.session.flush()

        return await self._get_by_owner_name(input_data.owner, input_data.name)

    async def list_all(self) -> list[RepositoryInfo]:
        """List all tracked repos ordered by created_at desc."""
        result = await self.session.execute(
            select(Repository).order_by(Repository.created_at.desc())
        )
        return [self._to_repo_domain(r) for r in result.scalars().all()]

    async def get_by_id(self, repo_id: UUID) -> RepositoryInfo | None:
        """Get a repo by ID."""
        result = await self.session.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()
        return self._to_repo_domain(repo) if repo else None

    async def _get_by_owner_name(self, owner: str, name: str) -> RepositoryInfo:
        """Internal: get repo by owner/name (raises if not found)."""
        result = await self.session.execute(
            select(Repository).where(
                Repository.owner == owner,
                Repository.name == name,
            )
        )
        repo = result.scalar_one()
        return self._to_repo_domain(repo)

    async def get_by_owner_name(self, owner: str, name: str) -> RepositoryInfo | None:
        """Get a repo by owner/name."""
        result = await self.session.execute(
            select(Repository).where(
                Repository.owner == owner,
                Repository.name == name,
            )
        )
        repo = result.scalar_one_or_none()
        return self._to_repo_domain(repo) if repo else None

    async def update_last_ingested(self, repo_id: UUID, timestamp: datetime) -> None:
        """Mark a repo as recently ingested."""
        result = await self.session.execute(select(Repository).where(Repository.id == repo_id))
        repo = result.scalar_one_or_none()
        if repo:
            repo.last_ingested_at = timestamp
            await self.session.flush()

    async def create_ingestion_run(self, repo_id: UUID) -> IngestionRunInfo:
        """Create a new ingestion run in RUNNING state."""
        run = IngestionRun(
            id=uuid4(),
            repository_id=repo_id,
            status=IngestionStatus.RUNNING.value,
            started_at=datetime.utcnow(),
        )
        self.session.add(run)
        await self.session.flush()
        return self._to_run_domain(run)

    async def complete_ingestion_run(
        self,
        run_id: UUID,
        status: IngestionStatus,
        error_message: str | None = None,
    ) -> None:
        """Complete an ingestion run (done or failed)."""
        result = await self.session.execute(
            select(IngestionRun).where(IngestionRun.id == run_id)
        )
        run = result.scalar_one_or_none()
        if run:
            run.status = status.value
            run.completed_at = datetime.utcnow()
            run.error_message = error_message
            await self.session.flush()

    async def list_ingestion_runs(self, repo_id: UUID) -> list[IngestionRunInfo]:
        """List ingestion runs for a repo, newest first."""
        result = await self.session.execute(
            select(IngestionRun)
            .where(IngestionRun.repository_id == repo_id)
            .order_by(IngestionRun.started_at.desc())
        )
        return [self._to_run_domain(r) for r in result.scalars().all()]

    async def get_ingestion_run(self, run_id: UUID) -> IngestionRunInfo | None:
        """Get a single ingestion run."""
        result = await self.session.execute(select(IngestionRun).where(IngestionRun.id == run_id))
        run = result.scalar_one_or_none()
        return self._to_run_domain(run) if run else None

    def _to_repo_domain(self, repo: Repository) -> RepositoryInfo:
        """Convert ORM Repository to domain RepositoryInfo."""
        return RepositoryInfo(
            id=repo.id,
            provider=repo.provider,
            owner=repo.owner,
            name=repo.name,
            default_branch=repo.default_branch,
            last_ingested_at=repo.last_ingested_at,
            created_at=repo.created_at,
        )

    def _to_run_domain(self, run: IngestionRun) -> IngestionRunInfo:
        """Convert ORM IngestionRun to domain IngestionRunInfo."""
        return IngestionRunInfo(
            id=run.id,
            repository_id=run.repository_id,
            status=IngestionStatus(run.status),
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_message=run.error_message,
        )
