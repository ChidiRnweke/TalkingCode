from dataclasses import dataclass
from logging import getLogger
from typing import Sequence

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

from .transformed_file import EmbeddingsWithMetadata, MetadataStore, PayloadStore

logger = getLogger("app_logger")


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class QdrantVectorStore(PayloadStore):
    qdrant_client: AsyncQdrantClient
    metadata_store: MetadataStore
    collection_name: str

    async def persist_embeddings(self, embeddings: EmbeddingsWithMetadata) -> None:
        logger.info(f"Storing embeddings for {embeddings.payload.file_name}")
        points = self._embeddings_to_point_struct(embeddings)
        await self.qdrant_client.upsert(self.collection_name, points)
        await self.metadata_store.mark_file_as_completed(embeddings.payload.document_id)
        logger.info(f"Embeddings stored for {embeddings.payload.file_name}")

    async def _create_if_not_exists(self, embedding: Sequence[float]) -> None:
        config = VectorParams(size=len(embedding), distance=Distance.COSINE)
        if not await self.qdrant_client.collection_exists(self.collection_name):
            await self.qdrant_client.create_collection(self.collection_name, config)

    def _embeddings_to_point_struct(
        self, embeddings: EmbeddingsWithMetadata
    ) -> list[PointStruct]:
        file_name = embeddings.payload.file_name
        repository_name = embeddings.payload.repository_name
        metadata = embeddings.payload.to_dict()
        ids = [
            f"{repository_name}/{file_name}/{i}" for i in range(len(embeddings.chunks))
        ]
        return [
            PointStruct(id=id, vector=chunk.embedding, payload=metadata)
            for chunk, id in zip(embeddings.chunks, ids)
        ]
