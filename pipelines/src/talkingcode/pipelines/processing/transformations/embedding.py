import asyncio
import logging
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI
from openai.types import CreateEmbeddingResponse

from talkingcode.pipelines.github_client import GitHubClient
from talkingcode.pipelines.models import FileMetadata, GitHubFile
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

from .transformed_file import EmbeddedChunk, Embedder

logger = logging.getLogger("app_logger")


@dataclass(frozen=True, slots=True)
class TextSplitter:
    chunk_size: int = 7000
    chunk_overlap: int = 500

    def split_text_to_chunks(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
            "cl100k_base",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        chunks = splitter.split_text(text)
        return chunks


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class OpenAIEmbedder(Embedder):
    """
    A TextEmbedder implementation that uses the OpenAI API to embed text.

    Args:
        api_client (AsyncOpenAI): The OpenAI API client to use.
        embedding_model (str): The name of the embedding model to use.
        github (GitHubClient): The GitHub client to use for fetching file content.
        splitter (TextSplitter): The text splitter to use for splitting text into chunks.
    """

    api_client: AsyncOpenAI
    splitter: TextSplitter
    github: GitHubClient
    embedding_model: str

    async def embed(self, file: FileMetadata) -> list[EmbeddedChunk]:
        file_content = await self.github.get_file_content(file.file)
        file_content = "Empty file" if len(file_content) == 0 else file_content
        split_file_content = self.splitter.split_text_to_chunks(file_content)
        enriched_content = [
            self._enrich_file_content(chunk, file.file) for chunk in split_file_content
        ]
        embeddings = await self._embed_document(enriched_content)
        return embeddings

    def _enrich_file_content(self, file_content: str, file: GitHubFile) -> str:
        file_name = f"\nThe file name is {file.name}.\n"
        file_place_in_project = f"The file is located at {file.path_in_project}.\n"
        file_extension = f"The file extension is {file.extension}.\n"
        return file_content + file_name + file_place_in_project + file_extension

    async def _embed_document(self, text: list[str]) -> list[EmbeddedChunk]:
        tasks: list[asyncio.Task[CreateEmbeddingResponse]] = []
        async with asyncio.TaskGroup() as tg:
            for chunk in text:
                embeddings = tg.create_task(
                    self.api_client.embeddings.create(
                        model=self.embedding_model, input=chunk
                    )
                )
                tasks.append(embeddings)
        responses = [embedding.result() for embedding in tasks]
        return [
            self._process_response(response, chunk)
            for response, chunk in zip(responses, text)
        ]

    def _process_response(
        self, response: CreateEmbeddingResponse, chunk_text: str
    ) -> EmbeddedChunk:
        embedding_vec = response.data[0].embedding
        embedding = EmbeddedChunk(text=chunk_text, embedding=embedding_vec)
        return embedding
