import asyncio
from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from talkingcode.pipelines.github_client import GitHubClient
from talkingcode.pipelines.models import FileMetadata
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time


class ToDict(Protocol):
    def to_dict(self) -> dict[str, Any]: ...


class MetadataStore(Protocol):
    async def get_all_repositories(self) -> Sequence[str]: ...
    async def get_file_metadata(
        self, repository_name: str
    ) -> Sequence[FileMetadata]: ...
    async def mark_file_as_completed(self, document_id: int) -> None: ...


@dataclass(frozen=True, slots=True)
class MergedTransformations:
    file_name: str
    repository_name: str
    document_id: int
    data: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "repository_name": self.repository_name,
            "document_id": self.document_id,
        } | self.data


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    text: str
    embedding: list[float]


@dataclass(frozen=True, slots=True)
class EmbeddingsWithPayload:
    payload: MergedTransformations
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
    def combine(cls, files: list["TransformedFile[T]"]) -> MergedTransformations:
        data = {k: v for file in files for k, v in file.data.to_dict().items()}

        return MergedTransformations(
            file_name=files[0].file_name,
            repository_name=files[0].repository_name,
            document_id=files[0].document_id,
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

    async def transform_repository(self, files: Sequence[FileMetadata]) -> None:
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
