import pytest
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from talkingcode.domain.models import RepositoryInfo, StartIngestionInput
from talkingcode.services.ingestion.ingestion_service import IngestionService


class FakeRepoRepo:
    async def register(self, input_data):
        pass

    async def get_by_id(self, rid):
        return RepositoryInfo(
            id=rid,
            provider="gh",
            owner="o",
            name="n",
            default_branch="main",
            last_ingested_at=None,
            created_at=datetime.now(timezone.utc),
        )

    async def create_ingestion_run(self, rid):
        return SimpleNamespace(id=uuid4())

    async def update_last_ingested(self, rid, dt):
        pass

    async def complete_ingestion_run(self, **kw):
        pass

    async def get_ingestion_run(self, rid):
        return None


class FakeDocRepo:
    pass


class FakeFetcher:
    async def fetch_file_tree(self, **kw):
        return []

    async def fetch_file_content(self, **kw):
        pass

    async def list_owned_repositories(self):
        return []


class FakeClassifier:
    pass


class FakeChunker:
    pass


class FakeEmbedder:
    model = "test-model"

    async def embed_batch(self, texts):
        return []


@pytest.mark.asyncio
async def test_run_ingestion_with_empty_tree():
    svc = IngestionService(
        repo_repository=FakeRepoRepo(),
        document_repository=FakeDocRepo(),
        github_fetcher=FakeFetcher(),
        classifier=FakeClassifier(),
        chunker=FakeChunker(),
        embedder=FakeEmbedder(),
        session_maker=None,
    )
    result = await svc.run_ingestion(
        StartIngestionInput(repository_id=uuid4())
    )
    assert result is not None
