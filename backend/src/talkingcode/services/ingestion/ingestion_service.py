"""Ingestion orchestrator service."""

import asyncio
import hashlib
import time
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
from talkingcode.telemetry.ingestion_metrics import get_ingestion_metrics

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)
metrics = get_ingestion_metrics()

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

        run_start = time.perf_counter()
        metrics.ingestion_runs_total.add(1, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "started"})
        logger.info("ingestion.run.started", run_id=str(run.id), repository=f"{repo.owner}/{repo.name}", git_ref=git_ref)

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
                    file_start = time.perf_counter()
                    logger.info("ingestion.file.started", run_id=str(run.id), repository=f"{repo.owner}/{repo.name}", git_ref=git_ref, path=path)

                    try:
                        async with file_processing_semaphore:
                            # stage: github fetch
                            t0 = time.perf_counter()
                            async with cast(asyncio.Semaphore, self.github_api_semaphore):
                                file_content = await self.github_fetcher.fetch_file_content(
                                    owner=repo.owner,
                                    name=repo.name,
                                    ref=git_ref,
                                    path=path,
                                )
                            fetch_sec = time.perf_counter() - t0
                            metrics.ingestion_github_request_duration_seconds.record(fetch_sec, attributes={"operation": "fetch_file_content", "provider": "github"})
                            logger.info("ingestion.file.stage.completed", stage="fetch", duration_ms=int(fetch_sec * 1000), path=path)

                            metrics.ingestion_file_size_bytes.record(len(file_content.content.encode("utf-8")), attributes={"repository": f"{repo.owner}/{repo.name}"})

                            content_sha = hashlib.sha256(
                                file_content.content.encode("utf-8")
                            ).hexdigest()

                            # stage: classify
                            t0 = time.perf_counter()
                            classification = await self._classify_with_fallback(
                                repo=f"{repo.owner}/{repo.name}",
                                path=path,
                                content=file_content.content,
                            )
                            classify_sec = time.perf_counter() - t0
                            metrics.ingestion_classification_duration_seconds.record(classify_sec, attributes={"repository": f"{repo.owner}/{repo.name}"})
                            logger.info("ingestion.file.stage.completed", stage="classify", duration_ms=int(classify_sec * 1000), path=path)

                            classification_dict = {
                                "language": classification.language,
                                "area": classification.area.value,
                                "file_type": classification.file_type.value,
                                "symbols": classification.symbols,
                                "tags": classification.tags,
                            }

                            # stage: chunk
                            t0 = time.perf_counter()
                            chunks = self.chunker.chunk(file_content.content)
                            chunk_sec = time.perf_counter() - t0
                            metrics.ingestion_chunking_duration_seconds.record(chunk_sec, attributes={"repository": f"{repo.owner}/{repo.name}"})
                            metrics.ingestion_chunk_count_per_file.record(len(chunks), attributes={"repository": f"{repo.owner}/{repo.name}"})
                            metrics.ingestion_chunks_total.add(len(chunks), attributes={"repository": f"{repo.owner}/{repo.name}"})
                            logger.info("ingestion.file.stage.completed", stage="chunk", duration_ms=int(chunk_sec * 1000), path=path, chunk_count=len(chunks))

                            # stage: embed
                            t0 = time.perf_counter()
                            embeddings: list[list[float]] = []
                            if chunks:
                                async with cast(asyncio.Semaphore, self.openrouter_api_semaphore):
                                    embeddings = await self.embedder.embed_batch(
                                        [chunk.content for chunk in chunks]
                                    )
                            embed_sec = time.perf_counter() - t0
                            metrics.ingestion_embedding_request_duration_seconds.record(embed_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "operation": "embed_batch"})
                            metrics.ingestion_embeddings_total.add(len(embeddings), attributes={"repository": f"{repo.owner}/{repo.name}"})
                            logger.info("ingestion.file.stage.completed", stage="embed", duration_ms=int(embed_sec * 1000), path=path, embedding_count=len(embeddings))

                            # stage: db write
                            t0 = time.perf_counter()
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
                            db_sec = time.perf_counter() - t0
                            metrics.ingestion_db_write_duration_seconds.record(db_sec, attributes={"repository": f"{repo.owner}/{repo.name}"})
                            logger.info("ingestion.file.stage.completed", stage="db_write", duration_ms=int(db_sec * 1000), path=path)

                            file_sec = time.perf_counter() - file_start
                            metrics.ingestion_files_total.add(1, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "success"})
                            metrics.ingestion_file_duration_seconds.record(file_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "success"})
                            logger.info("ingestion.file.completed", path=path, duration_ms=int(file_sec * 1000), status="success")

                            return True
                    except Exception as file_err:  # noqa: BLE001
                        file_sec = time.perf_counter() - file_start
                        metrics.ingestion_files_failed_total.add(1, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "failed"})
                        metrics.ingestion_file_duration_seconds.record(file_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "failed"})
                        logger.warning("ingestion.file.failed", path=path, duration_ms=int(file_sec * 1000), status="failed", error_code=type(file_err).__name__, error=str(file_err))
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

            run_sec = time.perf_counter() - run_start
            metrics.ingestion_run_duration_seconds.record(run_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "done"})
            logger.info("ingestion.run.completed", run_id=str(run.id), repository=f"{repo.owner}/{repo.name}", duration_ms=int(run_sec * 1000), status="done")

        except Exception as exc:  # noqa: BLE001
            run_sec = time.perf_counter() - run_start
            metrics.ingestion_run_duration_seconds.record(run_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "failed"})
            logger.error("ingestion.run.failed", run_id=str(run.id), repository=f"{repo.owner}/{repo.name}", duration_ms=int(run_sec * 1000), status="failed", error_code=type(exc).__name__, error=str(exc))
            
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
            metrics.ingestion_classifier_fallback_total.add(1, attributes={"operation": "classify", "status": "fallback"})
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
