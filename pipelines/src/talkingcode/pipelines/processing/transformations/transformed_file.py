import asyncio
from dataclasses import dataclass
from typing import Any, Protocol

from talkingcode.pipelines.github_client import GitHubClient
from talkingcode.pipelines.models import FileMetadata
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time


class ToDict[T](Protocol):
    transformation_name: str
    data: T

    def to_dict(self) -> dict[str, Any]: ...


class MetadataStore(Protocol):
    async def get_all_repositories(self) -> list[str]: ...
    async def get_file_metadata(self, repository_name: str) -> list[FileMetadata]: ...


@dataclass(frozen=True, slots=True)
class FinalPayload:
    file_name: str
    repository_name: str
    data: dict[str, dict[str, Any]]


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    text: str
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class EmbeddingsWithPayload:
    payload: FinalPayload
    chunks: list[EmbeddedChunk]


class PayloadStore(Protocol):
    async def save_payload(self, payload: EmbeddingsWithPayload) -> None: ...


@dataclass(frozen=True, slots=True)
class TransformedFile[T: ToDict]:
    repository_name: str
    document_id: int
    file_name: str
    data: T

    @classmethod
    def combine(cls, files: list["TransformedFile[T]"]) -> FinalPayload:
        data = {file.data.transformation_name: file.data.to_dict() for file in files}

        return FinalPayload(
            file_name=files[0].file_name,
            repository_name=files[0].repository_name,
            data=data,
        )


class Embedder(Protocol):
    async def embed(self, file: FileMetadata) -> list[EmbeddedChunk]: ...


class FileTransformation[T: ToDict](Protocol):
    async def transform(
        self, file: FileMetadata, file_content: str
    ) -> TransformedFile[T]: ...


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class TransformationPipeline:
    file_transformations: list[FileTransformation]
    metadata_store: MetadataStore
    embedder: Embedder
    github: GitHubClient
    payload_store: PayloadStore

    async def transform_all_repositories(self) -> None:
        repositories = await self.metadata_store.get_all_repositories()
        async with asyncio.TaskGroup() as tg:
            for repository in repositories:
                repo_files = await self.metadata_store.get_file_metadata(repository)
                tg.create_task(self.transform_repository(repo_files))

    async def transform_repository(self, files: list[FileMetadata]) -> None:
        transformation_tasks: list[list[asyncio.Task[TransformedFile]]] = []
        embedding_tasks: list[asyncio.Task[list[EmbeddedChunk]]] = []
        async with asyncio.TaskGroup() as tg:
            for file in files:
                file_transformations = []
                content = await self.github.get_file_content(file.file)
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
                _payload = EmbeddingsWithPayload(payload=payload, chunks=_embeddings)
                tg.create_task(self.payload_store.save_payload(_payload))
