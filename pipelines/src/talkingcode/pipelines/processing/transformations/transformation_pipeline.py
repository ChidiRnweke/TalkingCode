import asyncio
from dataclasses import dataclass
from logging import getLogger
from typing import Sequence

from talkingcode.pipelines.github_client import GitHubClient
from talkingcode.pipelines.models import FileMetadata
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

from .transformed_file import (
    EmbeddedChunk,
    Embedder,
    EmbeddingsWithMetadata,
    FileTransformation,
    MetadataStore,
    PayloadStore,
    TransformedFile,
)

logger = getLogger("app_logger")


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class TransformationPipeline:
    file_transformations: list[FileTransformation]
    metadata_store: MetadataStore
    embedder: Embedder
    github: GitHubClient
    payload_store: PayloadStore

    async def transform_all_repositories(self) -> None:
        logger.info("Starting transformation pipeline")
        repositories = await self.metadata_store.get_all_repositories()
        async with asyncio.TaskGroup() as tg:
            for repository in repositories:
                repo_files = await self.metadata_store.get_file_metadata(repository)
                logger.info(f"Processing repository {repository}")
                tg.create_task(self.transform_repository(repo_files))
        logger.info("Transformation pipeline completed")

    async def transform_repository(self, files: Sequence[FileMetadata]) -> None:
        transformation_tasks: list[list[asyncio.Task[TransformedFile]]] = []
        embedding_tasks: list[asyncio.Task[list[EmbeddedChunk]]] = []
        async with asyncio.TaskGroup() as tg:
            for file in files:
                file_transformations = []
                async with self.github as client:
                    content = await client.get_file_content(file.file)
                embedding_tasks.append(tg.create_task(self.embedder.embed(file)))
                for transformation in self.file_transformations:
                    transformed = tg.create_task(
                        transformation.transform(file, content)
                    )
                    file_transformations.append(transformed)

                transformation_tasks.append(file_transformations)

        async with asyncio.TaskGroup() as tg:
            for transformations, embeddings in zip(
                transformation_tasks, embedding_tasks
            ):
                _transforms = [t.result() for t in transformations]
                payload = TransformedFile.combine(_transforms)
                _embeddings = embeddings.result()
                _payload = EmbeddingsWithMetadata(payload=payload, chunks=_embeddings)
                tg.create_task(self.payload_store.persist_embeddings(_payload))
