"""Repository management routes."""

from fastapi import APIRouter
from pydantic import BaseModel
from talkingcode.dependencies import FactoryDep, IngestionAuthDep
from talkingcode.domain.models import (
    IngestionRunInfo,
    RegisterRepoInput,
    RepositoryInfo,
)

router = APIRouter()


class RegisterRepoRequest(BaseModel):
    """Request body for registering a repository."""

    owner: str
    name: str
    default_branch: str = "main"


class StartIngestionRequest(BaseModel):
    """Request body for starting an ingestion run."""

    git_ref: str | None = None


@router.post("/repos")
async def register_repo(
    body: RegisterRepoRequest,
    factory: FactoryDep,
    auth: IngestionAuthDep,
) -> RepositoryInfo:
    """Register a GitHub repository for ingestion."""
    controller = factory.get_ingestion_controller()
    repo = await controller.register_repo(
        RegisterRepoInput(
            owner=body.owner,
            name=body.name,
            default_branch=body.default_branch,
        )
    )
    return repo


@router.get("/repos")
async def list_repos(
    factory: FactoryDep, auth: IngestionAuthDep
) -> list[RepositoryInfo]:
    """List all tracked repositories."""
    controller = factory.get_ingestion_controller()
    repos = await controller.list_repos()
    return repos


@router.get("/repos/{owner}/{name}")
async def get_repo(owner: str, name: str, factory: FactoryDep) -> RepositoryInfo:
    """Get details of a specific repository."""
    controller = factory.get_ingestion_controller()
    repo = await controller.get_repo(owner, name)
    return repo


@router.post("/repos/{owner}/{name}/ingest")
async def start_ingestion(
    owner: str,
    name: str,
    factory: FactoryDep,
    auth: IngestionAuthDep,
    body: StartIngestionRequest | None = None,
) -> IngestionRunInfo:
    """Start an ingestion run. Synchronous — completes when ingestion is done."""
    controller = factory.get_ingestion_controller()
    git_ref = body.git_ref if body else None
    run = await controller.start_ingestion(owner, name, git_ref)
    return run


@router.post("/repos/ingest-owned")
async def start_owned_repo_ingestion(
    factory: FactoryDep,
    auth: IngestionAuthDep,
    body: StartIngestionRequest | None = None,
) -> list[IngestionRunInfo]:
    """Ingest all repositories owned by the authenticated user (excluding forks)."""
    controller = factory.get_ingestion_controller()
    git_ref = body.git_ref if body else None
    runs = await controller.start_owned_repo_ingestion(git_ref)
    return runs


@router.get("/repos/{owner}/{name}/runs")
async def list_ingestion_runs(
    owner: str,
    name: str,
    factory: FactoryDep,
) -> list[IngestionRunInfo]:
    """List ingestion run history for a repository."""
    controller = factory.get_ingestion_controller()
    runs = await controller.list_ingestion_runs(owner, name)
    return runs
