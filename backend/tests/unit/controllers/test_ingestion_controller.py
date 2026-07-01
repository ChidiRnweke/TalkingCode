import pytest
from uuid import uuid4
from datetime import datetime, timezone

from talkingcode.controllers.ingestion_controller import IngestionController
from talkingcode.domain.models import RepositoryInfo


class FakeRepoRepository:
    async def list_all(self):
        return [
            RepositoryInfo(
                id=uuid4(),
                provider="gh",
                owner="o",
                name="n",
                default_branch="main",
                last_ingested_at=None,
                created_at=datetime.now(timezone.utc),
            )
        ]

    async def get_by_owner_name(self, owner, name):
        return None

    async def register(self, input_data):
        pass

    async def list_ingestion_runs(self, repo_id):
        return []


class FakeIngestionService:
    async def run_ingestion(self, input_data):
        pass

    async def run_ingestion_for_owned_repos(self, git_ref=None):
        return []


@pytest.mark.asyncio
async def test_list_repos_returns_results():
    ctrl = IngestionController(
        repo_repository=FakeRepoRepository(),
        ingestion_service=FakeIngestionService(),
    )
    result = await ctrl.list_repos()
    assert len(result) == 1
