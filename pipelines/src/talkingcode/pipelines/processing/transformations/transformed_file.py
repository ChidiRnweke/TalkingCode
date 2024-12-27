from dataclasses import dataclass
from typing import Any, Protocol, Sequence

from talkingcode.pipelines.models import FileMetadata


class PayloadStore(Protocol):
    async def persist_embeddings(
        self, embeddings: "EmbeddingsWithMetadata"
    ) -> None: ...


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
class EmbeddingsWithMetadata:
    payload: MergedTransformations
    chunks: list[EmbeddedChunk]


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
