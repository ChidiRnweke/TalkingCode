import asyncio
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Type

from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from talkingcode.pipelines.models import FileMetadata
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

from .transformed_file import FileTransformation, TransformedFile

logger = getLogger("app_logger")

_openai_enrichment_semaphore = asyncio.Semaphore(5)


class IdentifiedTopics(BaseModel):
    data: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"topics": self.data}


class FileSummary(BaseModel):
    data: str
    transformation_name: str = "file_summary"

    def to_dict(self) -> dict[str, Any]:
        return {"file_summary": self.data}


@dataclass(frozen=True, slots=True)
class Metadata:
    path_in_repo: str
    extension: str
    url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_in_repo": self.path_in_repo,
            "extension": self.extension,
            "url": self.url,
        }


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class TopicsEnrichment(FileTransformation[IdentifiedTopics]):
    openai: AsyncOpenAI
    metadata_prompt: str
    model: str = "gpt-4o-mini"

    async def transform(
        self, file: FileMetadata, file_content: str
    ) -> TransformedFile[IdentifiedTopics]:
        _topics = await _fetch_openai_response(
            self.openai,
            self.model,
            self.metadata_prompt,
            file,
            file_content,
            IdentifiedTopics,
        )

        topics = _topics.choices[0].message.parsed
        if not topics:
            logger.warning(f"No topics could be identified for file {file.file}")
            topics = IdentifiedTopics(data=[])

        return TransformedFile(
            repository_name=file.repository_name,
            document_id=file.document_id,
            file_name=file.file.name,
            data=topics,
        )


@dataclass(frozen=True, slots=True)
class MetadataEnricher(FileTransformation[Metadata]):
    async def transform(
        self, file: FileMetadata, file_content: str
    ) -> TransformedFile[Metadata]:
        url = file.file.content_url
        path_in_repo = file.file.path_in_project
        extension = file.file.extension

        metadata = Metadata(path_in_repo=path_in_repo, extension=extension, url=url)
        return TransformedFile(
            repository_name=file.repository_name,
            document_id=file.document_id,
            file_name=file.file.name,
            data=metadata,
        )


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class OpenAIMetadataEnricher(FileTransformation[FileSummary]):
    openai: AsyncOpenAI
    summary_prompt: str
    model: str = "gpt-4o-mini"

    async def transform(
        self, file: FileMetadata, file_content: str
    ) -> TransformedFile[FileSummary]:
        _summary = await _fetch_openai_response(
            self.openai,
            self.model,
            self.summary_prompt,
            file,
            file_content,
            FileSummary,
        )

        summary = _summary.choices[0].message.parsed
        if not summary:
            no_summary = f"No summary could be identified for file {file.file}"
            logger.warning(no_summary)
            summary = FileSummary(data=no_summary)

        return TransformedFile(
            repository_name=file.repository_name,
            document_id=file.document_id,
            file_name=file.file.name,
            data=summary,
        )


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=20))
async def _fetch_openai_response[A](
    client: AsyncOpenAI,
    model: str,
    prompt: str,
    file: FileMetadata,
    content: str,
    response_format: Type[A],
):
    enriched = file.file.enrich_content(content)
    async with _openai_enrichment_semaphore:
        return await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": enriched},
            ],
            response_format=response_format,
        )
