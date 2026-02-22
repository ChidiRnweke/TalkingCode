"""Repository management routes."""

from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from talkingcode.dependencies import FactoryDep
from talkingcode.domain.models import IngestionRunInfo, RegisterRepoInput, RepositoryInfo

router = APIRouter()


class RegisterRepoRequest(BaseModel):
    """Request body for registering a repository."""

    owner: str
    name: str
    default_branch: str = "main"


class StartIngestionRequest(BaseModel):
    """Request body for starting an ingestion run."""

    git_ref: str | None = None


def _to_iso(value: datetime | None) -> str | None:
    """Convert optional datetime to ISO string."""
    return value.isoformat() if value else None


def _serialize_repo(repo: RepositoryInfo) -> dict[str, str | None]:
    """Serialize a RepositoryInfo to a JSON-safe dict."""
    data = asdict(repo)
    return {
        "id": str(data["id"]),
        "provider": data["provider"],
        "owner": data["owner"],
        "name": data["name"],
        "default_branch": data["default_branch"],
        "last_ingested_at": _to_iso(data["last_ingested_at"]),
        "created_at": data["created_at"].isoformat(),
    }


def _serialize_run(run: IngestionRunInfo) -> dict[str, str | None]:
    """Serialize an IngestionRunInfo to a JSON-safe dict."""
    data = asdict(run)
    return {
        "id": str(data["id"]),
        "repository_id": str(data["repository_id"]),
        "status": data["status"].value,
        "started_at": data["started_at"].isoformat(),
        "completed_at": _to_iso(data["completed_at"]),
        "error_message": data["error_message"],
    }


@router.post("/repos")
async def register_repo(body: RegisterRepoRequest, factory: FactoryDep) -> dict[str, str | None]:
    """Register a GitHub repository for ingestion."""
    controller = factory.get_ingestion_controller()
    repo = await controller.register_repo(
        RegisterRepoInput(
            owner=body.owner,
            name=body.name,
            default_branch=body.default_branch,
        )
    )
    return _serialize_repo(repo)


@router.get("/repos")
async def list_repos(factory: FactoryDep) -> list[dict[str, str | None]]:
    """List all tracked repositories."""
    controller = factory.get_ingestion_controller()
    repos = await controller.list_repos()
    return [_serialize_repo(repo) for repo in repos]


@router.get("/repos/{owner}/{name}")
async def get_repo(owner: str, name: str, factory: FactoryDep) -> dict[str, str | None]:
    """Get details of a specific repository."""
    controller = factory.get_ingestion_controller()
    repo = await controller.get_repo(owner, name)
    return _serialize_repo(repo)


@router.post("/repos/{owner}/{name}/ingest")
async def start_ingestion(
    owner: str,
    name: str,
    factory: FactoryDep,
    body: StartIngestionRequest | None = None,
) -> dict[str, str | None]:
    """Start an ingestion run. Synchronous — completes when ingestion is done."""
    controller = factory.get_ingestion_controller()
    git_ref = body.git_ref if body else None
    run = await controller.start_ingestion(owner, name, git_ref)
    return _serialize_run(run)


@router.get("/repos/{owner}/{name}/runs")
async def list_ingestion_runs(
    owner: str,
    name: str,
    factory: FactoryDep,
) -> list[dict[str, str | None]]:
    """List ingestion run history for a repository."""
    controller = factory.get_ingestion_controller()
    runs = await controller.list_ingestion_runs(owner, name)
    return [_serialize_run(run) for run in runs]
