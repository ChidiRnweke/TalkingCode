"""Ingestion orchestrator service."""

import asyncio
import hashlib
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any, Protocol, cast
from uuid import UUID

import structlog

from talkingcode.domain.models import (
    DocumentClassificationInput,
    DocumentClassificationOutput,
    IngestionRunInfo,
    RegisterRepoInput,
    StartIngestionInput,
)
from talkingcode.enums import Area, FileType
from talkingcode.enums import IngestionStatus
from talkingcode.errors import NotFoundError
from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.repository.database import get_engine, get_session, get_session_maker
from talkingcode.repository.repo_repository import RepoRepository
from talkingcode.services.classification.document_classifier import IDocumentClassifier
from talkingcode.services.ingestion.chunker import IChunker
from talkingcode.services.ingestion.embedder import IEmbedder
from talkingcode.services.ingestion.github_fetcher import IGitHubFetcher

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)
OWNED_REPO_INGEST_CONCURRENCY = 4
FILE_INGEST_CONCURRENCY = 12
GITHUB_API_CONCURRENCY = 6
OPENROUTER_API_CONCURRENCY = 3


class IIngestionService(Protocol):
    """Protocol for ingestion orchestration."""

    async def run_ingestion(self, input_data: StartIngestionInput) -> IngestionRunInfo:
        """Run a full ingestion pipeline for a repository."""
        ...

    async def run_ingestion_for_owned_repos(
        self, git_ref: str | None = None
    ) -> list[IngestionRunInfo]:
        """Ingest all non-fork repositories owned by the current GitHub user."""
        ...


@dataclass(slots=True)
class IngestionService:
    """Orchestrates the full ingestion pipeline."""

    repo_repository: RepoRepository
    document_repository: DocumentRepository
    github_fetcher: IGitHubFetcher
    classifier: IDocumentClassifier
    chunker: IChunker
    embedder: IEmbedder
    database_url: str
    github_api_semaphore: asyncio.Semaphore | None = None
    openrouter_api_semaphore: asyncio.Semaphore | None = None

    def __post_init__(self) -> None:
        """Initialize shared rate-limit semaphores."""
        if self.github_api_semaphore is None:
            self.github_api_semaphore = asyncio.Semaphore(GITHUB_API_CONCURRENCY)
        if self.openrouter_api_semaphore is None:
            self.openrouter_api_semaphore = asyncio.Semaphore(OPENROUTER_API_CONCURRENCY)

    async def run_ingestion_for_owned_repos(
        self, git_ref: str | None = None
    ) -> list[IngestionRunInfo]:
        """Register and ingest all non-fork repositories owned by the current user."""
        repositories = await self.github_fetcher.list_owned_repositories()

        logger.info("Starting owned repo ingestion", repo_count=len(repositories), ref=git_ref)

        semaphore = asyncio.Semaphore(OWNED_REPO_INGEST_CONCURRENCY)

        async def ingest_single(repo: Any) -> IngestionRunInfo | None:
            try:
                async with semaphore:
                    async with get_session(self.database_url) as session:
                        local_repo_repository = RepoRepository(session)
                        local_document_repository = DocumentRepository(session)
                        local_service = IngestionService(
                            repo_repository=local_repo_repository,
                            document_repository=local_document_repository,
                            github_fetcher=self.github_fetcher,
                            classifier=self.classifier,
                            chunker=self.chunker,
                            embedder=self.embedder,
                            database_url=self.database_url,
                            github_api_semaphore=self.github_api_semaphore,
                            openrouter_api_semaphore=self.openrouter_api_semaphore,
                        )

                        registered_repo = await local_repo_repository.register(
                            RegisterRepoInput(
                                owner=repo.owner,
                                name=repo.name,
                                default_branch=repo.default_branch,
                            )
                        )
                        await session.commit()

                        return await local_service.run_ingestion(
                            StartIngestionInput(repository_id=registered_repo.id, git_ref=git_ref)
                        )
            except Exception as repo_err:  # noqa: BLE001
                logger.error(
                    "Owned repo ingestion failed; continuing",
                    owner=repo.owner,
                    name=repo.name,
                    error=str(repo_err),
                )
                return None

        tasks: list[asyncio.Task[IngestionRunInfo | None]] = []
        async with asyncio.TaskGroup() as tg:
            for repo in repositories:
                tasks.append(tg.create_task(ingest_single(repo)))

        completed_runs = [task.result() for task in tasks]
        runs = cast(list[IngestionRunInfo], [run for run in completed_runs if run is not None])

        logger.info("Completed owned repo ingestion", ingested_repo_count=len(runs))
        return runs

    async def run_ingestion(self, input_data: StartIngestionInput) -> IngestionRunInfo:
        """Run a full ingestion pipeline."""
        repo = await self.repo_repository.get_by_id(input_data.repository_id)
        if not repo:
            raise NotFoundError(resource=f"Repository {input_data.repository_id}")

        git_ref = input_data.git_ref or repo.default_branch
        run = await self.repo_repository.create_ingestion_run(repo.id)

        logger.info(
            "Starting ingestion",
            repo=f"{repo.owner}/{repo.name}",
            ref=git_ref,
            run_id=str(run.id),
        )

        try:
            paths = await self.github_fetcher.fetch_file_tree(
                owner=repo.owner,
                name=repo.name,
                ref=git_ref,
            )
            logger.info("File tree fetched", file_count=len(paths))
            engine = get_engine(self.database_url)
            session_maker = get_session_maker(engine)
            file_processing_semaphore = asyncio.Semaphore(FILE_INGEST_CONCURRENCY)

            try:
                async def ingest_file(path: str) -> bool:
                    logger.info("Ingesting file", path=path)
                    try:
                        async with file_processing_semaphore:
                            async with cast(asyncio.Semaphore, self.github_api_semaphore):
                                file_content = await self.github_fetcher.fetch_file_content(
                                    owner=repo.owner,
                                    name=repo.name,
                                    ref=git_ref,
                                    path=path,
                                )

                            content_sha = hashlib.sha256(
                                file_content.content.encode("utf-8")
                            ).hexdigest()

                            classification = await self._classify_with_fallback(
                                repo=f"{repo.owner}/{repo.name}",
                                path=path,
                                content=file_content.content,
                            )
                            classification_dict = {
                                "language": classification.language,
                                "area": classification.area.value,
                                "file_type": classification.file_type.value,
                                "symbols": classification.symbols,
                                "tags": classification.tags,
                            }

                            chunks = self.chunker.chunk(file_content.content)

                            embeddings: list[list[float]] = []
                            if chunks:
                                async with cast(asyncio.Semaphore, self.openrouter_api_semaphore):
                                    embeddings = await self.embedder.embed_batch(
                                        [chunk.content for chunk in chunks]
                                    )

                            async with session_maker() as session:
                                local_document_repository = DocumentRepository(session)
                                try:
                                    doc_id = await local_document_repository.save_document(
                                        repository_id=repo.id,
                                        path=path,
                                        content_sha=content_sha,
                                        git_ref=git_ref,
                                        classification=classification_dict,
                                    )

                                    if chunks and embeddings:
                                        if len(chunks) != len(embeddings):
                                            raise ValueError("Chunk/embedding count mismatch")

                                        chunk_ids: list[UUID] = []
                                        for chunk in chunks:
                                            chunk_id = await local_document_repository.save_chunk(
                                                document_id=doc_id,
                                                chunk_index=chunk.chunk_index,
                                                content=chunk.content,
                                                token_count=chunk.token_count,
                                                metadata=classification_dict,
                                            )
                                            chunk_ids.append(chunk_id)

                                        for chunk_id, embedding in zip(
                                            chunk_ids, embeddings, strict=True
                                        ):
                                            await local_document_repository.save_chunk_embedding(
                                                chunk_id=chunk_id,
                                                embedding=embedding,
                                                model=self.embedder.model,
                                            )

                                    await session.commit()
                                except Exception:
                                    await session.rollback()
                                    raise

                            return True
                    except Exception as file_err:  # noqa: BLE001
                        logger.warning(
                            "Failed to ingest file, skipping",
                            path=path,
                            error=str(file_err),
                        )
                        return False

                tasks: list[asyncio.Task[bool]] = []
                async with asyncio.TaskGroup() as tg:
                    for path in paths:
                        tasks.append(tg.create_task(ingest_file(path)))

                ingested_files = sum(1 for task in tasks if task.result())
                logger.info(
                    "Completed repo file ingestion",
                    repo=f"{repo.owner}/{repo.name}",
                    ingested_files=ingested_files,
                    total_files=len(paths),
                )
            finally:
                await engine.dispose()

            await self.repo_repository.update_last_ingested(repo.id, datetime.utcnow())
            await self.repo_repository.complete_ingestion_run(
                run_id=run.id,
                status=IngestionStatus.DONE,
            )

            logger.info(
                "Ingestion completed",
                repo=f"{repo.owner}/{repo.name}",
                run_id=str(run.id),
            )

        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Ingestion failed",
                repo=f"{repo.owner}/{repo.name}",
                error=str(exc),
            )
            await self.repo_repository.complete_ingestion_run(
                run_id=run.id,
                status=IngestionStatus.FAILED,
                error_message=str(exc),
            )

        final_run = await self.repo_repository.get_ingestion_run(run.id)
        return final_run or run

    async def _classify_with_fallback(
        self,
        repo: str,
        path: str,
        content: str,
    ) -> DocumentClassificationOutput:
        """Classify with LLM and degrade to heuristic on failure."""
        try:
            async with cast(asyncio.Semaphore, self.openrouter_api_semaphore):
                return await self.classifier.classify(
                    DocumentClassificationInput(
                        repo=repo,
                        path=path,
                        content=content[:2000],
                    )
                )
        except Exception as classification_err:  # noqa: BLE001
            logger.warning(
                "Classifier failed, using heuristic classification",
                path=path,
                error=str(classification_err),
            )
            return self._heuristic_classification(path=path, content=content)

    def _heuristic_classification(self, path: str, content: str) -> DocumentClassificationOutput:
        """Fallback classifier when model classification fails."""
        lower = path.lower()

        if "/tests/" in lower or lower.startswith("tests/") or lower.endswith("_test.py"):
            area = "tests"
            file_type = "test"
        elif lower.endswith(('.md', '.rst', '.txt')):
            area = "docs"
            file_type = "docs"
        elif any(part in lower for part in ["docker", ".github/", "terraform", ".tf", ".hcl"]):
            area = "infra"
            file_type = "config"
        elif "/frontend/" in lower or lower.endswith((".svelte", ".tsx", ".jsx", ".css", ".html")):
            area = "frontend"
            file_type = "source"
        elif "/backend/" in lower or lower.endswith((".py", ".go", ".rs", ".java", ".rb")):
            area = "backend"
            file_type = "source"
        else:
            area = "unknown"
            file_type = "unknown"

        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        language_map = {
            "py": "python",
            "ts": "typescript",
            "tsx": "typescript",
            "js": "javascript",
            "jsx": "javascript",
            "svelte": "svelte",
            "go": "go",
            "rs": "rust",
            "java": "java",
            "rb": "ruby",
            "md": "markdown",
            "sql": "sql",
            "yaml": "yaml",
            "yml": "yaml",
            "json": "json",
            "toml": "toml",
            "sh": "shell",
            "css": "css",
            "html": "html",
        }
        language = language_map.get(ext, "")

        symbol_matches = re.findall(r"\b(?:def|class|function|interface|type)\s+([A-Za-z_][A-Za-z0-9_]*)", content)

        return DocumentClassificationOutput(
            language=language,
            area=Area(area),
            file_type=FileType(file_type),
            symbols=symbol_matches[:30],
            tags=[],
        )
