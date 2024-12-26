import asyncio
from dataclasses import dataclass
from logging import getLogger
from typing import Protocol, Type

from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.shared.database import (
    FileSummaryModel,
    FileTopicModel,
    GithubFileModel,
    GitHubRepositoryModel,
    RepositorySummaryModel,
)

from .ingestion import GitHubClient
from .models import FileMetadata

logger = getLogger("app_logger")

_openai_enrichment_semaphore = asyncio.Semaphore(10)


class IdentifiedTopics(BaseModel):
    topics: list[str]


class FileSummary(BaseModel):
    summary: str


@dataclass(frozen=True, slots=True)
class TransformedFile[T]:
    repository_name: str
    document_id: int
    name: str
    data: T


@dataclass(frozen=True, slots=True)
class EnrichedMetadata:
    topics: list[str]
    summary: str


class RepositoryRetriever(Protocol):
    async def get_all_repositories(self) -> list[str]: ...
    async def get_file_metadata(self, repository_name: str) -> list[FileMetadata]: ...
    async def get_file_summaries(
        self, repository_name: str
    ) -> list[TransformedFile[FileSummary]]: ...


class EnrichmentPersistence(Protocol):
    async def save_enriched_metadata(
        self, file: TransformedFile[EnrichedMetadata]
    ) -> None: ...

    async def save_repository_summary(
        self, repository_name: str, summary: str
    ) -> None: ...


class FileTransformation[T](Protocol):
    async def transform(self, file: FileMetadata) -> TransformedFile[T]: ...


@dataclass(frozen=True, slots=True)
class EnrichmentPipeline:
    retriever: RepositoryRetriever
    transformer: FileTransformation[EnrichedMetadata]
    storage: EnrichmentPersistence

    async def enrich_all_repositories(self) -> None:
        repositories = await self.retriever.get_all_repositories()
        async with asyncio.TaskGroup() as tg:
            for repository in repositories:
                tg.create_task(self._enrich_repository_with_files(repository))

    async def _enrich_repository_with_files(self, repository_name: str) -> None:
        files = await self.retriever.get_file_metadata(repository_name)
        async with asyncio.TaskGroup() as tg:
            for file in files:
                tg.create_task(self._enrich_file(file))
        await self._enrich_repository(repository_name)

    async def _enrich_file(self, file: FileMetadata) -> None:
        transformed_file = await self.transformer.transform(file)
        await self.storage.save_enriched_metadata(transformed_file)

    async def _enrich_repository(self, repository_name: str) -> None:
        summarizer = RepositorySummarizer(
            openai=AsyncOpenAI(),
            retriever=self.retriever,
            repository_summarizer_prompt="Summarize the repository",
        )
        summary = await summarizer.summarize_repository(repository_name)
        await self.storage.save_repository_summary(repository_name, summary)


@dataclass(frozen=True, slots=True)
class GithubRepositoryRetriever(RepositoryRetriever):
    session: AsyncSession

    async def get_all_repositories(self) -> list[str]:
        stmt = select(GitHubRepositoryModel.name)
        result = (await self.session.scalars(stmt)).all()
        if not result:
            logger.warning("No repositories found, have you already ingested data?")
            raise ValueError("No repositories found, have you already ingested data?")
        return list(result)

    async def get_file_metadata(self, repository_name: str) -> list[FileMetadata]:
        stmt = select(GithubFileModel).where(
            GitHubRepositoryModel.name == repository_name
        )
        files = (await self.session.scalars(stmt)).all()
        if not files:
            logger.warning(f"No files found for repository {repository_name}")
            raise ValueError(f"No files found for repository {repository_name}")
        return [FileMetadata.from_db_object(file) for file in files]

    async def get_file_summaries(
        self, repository_name: str
    ) -> list[TransformedFile[FileSummary]]:
        stmt = (
            select(GithubFileModel)
            .where(GitHubRepositoryModel.name == repository_name)
            .join(FileSummaryModel)
        )

        files = (await self.session.scalars(stmt)).all()
        if not files:
            logger.warning(f"No files found for repository {repository_name}")
            raise ValueError(f"No files found for repository {repository_name}")
        return [
            TransformedFile(
                repository_name=file.repository_name,
                document_id=file.id,
                name=file.name,
                data=FileSummary(summary=file.summary.text),
            )
            for file in files
        ]


@dataclass(frozen=True, slots=True)
class PostgresEnrichmentStorage(EnrichmentPersistence):
    session: AsyncSession

    async def save_enriched_metadata(
        self, file: TransformedFile[EnrichedMetadata]
    ) -> None:
        for topic in file.data.topics:
            topic_model = FileTopicModel(document_id=file.document_id, topic=topic)
            summary_model = FileSummaryModel(
                document_id=file.document_id, summary=file.data.summary
            )
            self.session.add(topic_model)
            self.session.add(summary_model)
        await self.session.commit()

    async def save_repository_summary(self, repository_name: str, summary: str) -> None:
        repository_summary = RepositorySummaryModel(
            repository_name=repository_name, summary=summary
        )
        self.session.add(repository_summary)
        await self.session.commit()


@dataclass(frozen=True, slots=True)
class RepositorySummarizer:
    openai: AsyncOpenAI
    retriever: RepositoryRetriever
    repository_summarizer_prompt: str
    model: str = "gpt-4o-mini"

    async def summarize_repository(self, repository_name: str) -> str:
        files = await self.retriever.get_file_summaries(repository_name)
        openai_format = self._to_openai_format(files)
        async with _openai_enrichment_semaphore:
            response = await self.openai.chat.completions.create(
                model=self.model,
                messages=openai_format,  # type: ignore
            )
        if not (message := response.choices[0].message.content):
            base = "No summary could be generated for repository"
            logger.warning(f"{base} {repository_name}")
            return base
        else:
            return message

    def _to_openai_format(self, files: list[TransformedFile[FileSummary]]):
        system_prompt = {
            "role": "system",
            "content": self.repository_summarizer_prompt,
        }
        files_content = []
        for file in files:
            summary = file.data.summary
            text = f"[FILE SUMMARY BEGIN] repo: {file.repository_name}, file_name: {file.name} summary: {summary} [FILE SUMMARY END]"
            files_content.append(text)
        return [system_prompt, {"role": "user", "content": "\n".join(files_content)}]


@dataclass(frozen=True, slots=True)
class OpenAIMetadataEnricher(FileTransformation[EnrichedMetadata]):
    openai: AsyncOpenAI
    github: GitHubClient
    metadata_prompt: str
    summary_prompt: str
    model: str = "gpt-4o-mini"

    async def transform(self, file: FileMetadata) -> TransformedFile[EnrichedMetadata]:
        file_content = await self.github.get_file_content(file.file)
        async with asyncio.TaskGroup() as tg:
            _topics = tg.create_task(
                self._fetch_openai_response(
                    self.metadata_prompt,
                    file,
                    file_content,
                    IdentifiedTopics,
                )
            )
            _summary = tg.create_task(
                self._fetch_openai_response(
                    self.summary_prompt,
                    file,
                    file_content,
                    FileSummary,
                )
            )

        topics = _topics.result().choices[0].message.parsed
        summary = _summary.result().choices[0].message.parsed
        if not topics:
            logger.warning(f"No topics could be identified for file {file.file}")
            topics = IdentifiedTopics(topics=[])
        if not summary:
            no_summary = f"No summary could be identified for file {file.file}"
            logger.warning(no_summary)
            summary = FileSummary(summary=no_summary)
        metadata = EnrichedMetadata(topics=topics.topics, summary=summary.summary)
        return TransformedFile(
            repository_name=file.repository_name,
            document_id=file.document_id,
            name=file.file.name,
            data=metadata,
        )

    async def _fetch_openai_response[A](
        self, prompt: str, file: FileMetadata, content: str, response_format: Type[A]
    ):
        async with _openai_enrichment_semaphore:
            return await self.openai.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": f"repo: {file.repository_name}, file: {file.file} content: {content}",
                    },
                ],
                response_format=response_format,
            )
