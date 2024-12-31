import asyncio
from dataclasses import dataclass
from typing import ClassVar, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tenacity import retry, stop_after_attempt, wait_exponential

from talkingcode.pipelines.database import GithubFileModel, GitHubRepositoryModel
from talkingcode.pipelines.models import FileMetadata

from .transformed_file import MetadataStore


@dataclass(frozen=True, slots=True)
class MetadataStorageService(MetadataStore):
    session: async_sessionmaker[AsyncSession]
    allowed_extensions: Sequence[str]
    disallowed_files: Sequence[str]
    sync_mode: bool = False
    _db_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    """
    A metadata storage service that interacts with the database to store and retrieve metadata about files and repositories.

    Args:
        session (async_sessionmaker[AsyncSession]): The SQLAlchemy async session to use for interacting with the database.
    """

    async def get_all_repositories(self) -> Sequence[str]:
        if self.sync_mode:
            result = await self._get_all_repositories()
        else:
            result = await self._get_all_repositories()
        return result

    async def get_file_metadata(self, repository_name: str) -> Sequence[FileMetadata]:
        if self.sync_mode:
            result = await self._get_file_metadata(repository_name)
        else:
            result = await self._get_file_metadata(repository_name)
        return result

    @retry(
        stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    async def mark_files_as_completed(self, document_ids: list[int]) -> None:
        if self.sync_mode:
            result = await self._mark_files_as_completed(document_ids)
        else:
            result = await self._mark_files_as_completed(document_ids)
        return result

    async def _get_file_metadata(self, repository_name: str) -> Sequence[FileMetadata]:
        stmt = (
            select(GithubFileModel)
            .where(GithubFileModel.repository_name == repository_name)
            .where(GithubFileModel.is_embedded.is_(False))
            .where(GithubFileModel.name.not_in(self.disallowed_files))
            .where(GithubFileModel.file_extension.in_(self.allowed_extensions))
        )
        async with self.session() as session:
            result = await session.scalars(stmt)
            files = result.all()
            return [FileMetadata.from_db_object(file) for file in files]

    async def _get_all_repositories(self) -> Sequence[str]:
        stmt = select(GitHubRepositoryModel.name)
        async with self.session() as session:
            result = await session.scalars(stmt)
            return result.all()

    @retry(
        stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1, min=4, max=20)
    )
    async def _mark_files_as_completed(self, document_ids: list[int]) -> None:
        stmt = (
            update(GithubFileModel)
            .where(GithubFileModel.id.in_(document_ids))
            .values(is_embedded=True)
        )
        async with self.session() as session:
            await session.execute(stmt)
            await session.commit()
