"""Ingestion orchestrator service."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

import structlog

from talkingcode.domain.models import (
    DocumentClassificationInput,
    IngestionRunInfo,
    StartIngestionInput,
)
from talkingcode.enums import IngestionStatus
from talkingcode.errors import NotFoundError
from talkingcode.repository.document_repository import DocumentRepository
from talkingcode.repository.repo_repository import RepoRepository
from talkingcode.services.classification.document_classifier import IDocumentClassifier
from talkingcode.services.ingestion.chunker import IChunker
from talkingcode.services.ingestion.embedder import IEmbedder
from talkingcode.services.ingestion.github_fetcher import IGitHubFetcher

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


class IIngestionService(Protocol):
    """Protocol for ingestion orchestration."""

    async def run_ingestion(self, input_data: StartIngestionInput) -> IngestionRunInfo:
        """Run a full ingestion pipeline for a repository."""


@dataclass(slots=True)
class IngestionService:
    """Orchestrates the full ingestion pipeline."""

    repo_repository: RepoRepository
    document_repository: DocumentRepository
    github_fetcher: IGitHubFetcher
    classifier: IDocumentClassifier
    chunker: IChunker
    embedder: IEmbedder

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

            for idx, path in enumerate(paths):
                logger.info(
                    "Ingesting file",
                    progress=f"{idx + 1}/{len(paths)}",
                    path=path,
                )

                try:
                    file_content = await self.github_fetcher.fetch_file_content(
                        owner=repo.owner,
                        name=repo.name,
                        ref=git_ref,
                        path=path,
                    )

                    content_sha = hashlib.sha256(
                        file_content.content.encode("utf-8")
                    ).hexdigest()

                    classification = await self.classifier.classify(
                        DocumentClassificationInput(
                            repo=f"{repo.owner}/{repo.name}",
                            path=path,
                            content=file_content.content[:2000],
                        )
                    )

                    classification_dict = {
                        "language": classification.language,
                        "area": classification.area.value,
                        "file_type": classification.file_type.value,
                        "symbols": classification.symbols,
                        "tags": classification.tags,
                    }

                    doc_id = await self.document_repository.save_document(
                        repository_id=repo.id,
                        path=path,
                        content_sha=content_sha,
                        git_ref=git_ref,
                        classification=classification_dict,
                    )

                    chunks = self.chunker.chunk(file_content.content)
                    if not chunks:
                        continue

                    chunk_ids: list[UUID] = []
                    chunk_texts: list[str] = []

                    for chunk in chunks:
                        chunk_id = await self.document_repository.save_chunk(
                            document_id=doc_id,
                            chunk_index=chunk.chunk_index,
                            content=chunk.content,
                            token_count=chunk.token_count,
                            metadata=classification_dict,
                        )
                        chunk_ids.append(chunk_id)
                        chunk_texts.append(chunk.content)

                    embeddings = await self.embedder.embed_batch(chunk_texts)

                    for chunk_id, embedding in zip(chunk_ids, embeddings, strict=True):
                        await self.document_repository.save_chunk_embedding(
                            chunk_id=chunk_id,
                            embedding=embedding,
                            model=self.embedder.model,
                        )

                except Exception as file_err:  # noqa: BLE001
                    logger.warning(
                        "Failed to ingest file, skipping",
                        path=path,
                        error=str(file_err),
                    )
                    continue

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
