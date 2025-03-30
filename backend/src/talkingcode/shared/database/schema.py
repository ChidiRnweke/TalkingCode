from datetime import datetime

from sqlalchemy import DateTime, ForeignKeyConstraint, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


class PipelineRunModel(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(default=False)
    error_message: Mapped[str] = mapped_column(String(255), nullable=True)

    associated_schedule: Mapped[str] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["associated_schedule"],
            ["pipeline_schedule.id"],
        ),
    )


class PipelineScheduleModel(Base):
    __tablename__ = "pipeline_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    schedule_start_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    start_hour: Mapped[int] = mapped_column(Integer)
    start_minute: Mapped[int] = mapped_column(Integer)

    is_active: Mapped[bool] = mapped_column(default=True)


class TokenSpendModel(Base):
    __tablename__ = "tokens_spent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(255))
    token_count: Mapped[int] = mapped_column(Integer)
    model: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class GitHubRepositoryModel(Base):
    __tablename__ = "github_repositories"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    user: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    url: Mapped[str] = mapped_column(String(255))

    files: Mapped[list["GithubFileModel"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )


class GithubFileModel(Base):
    __tablename__ = "github_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    content_url: Mapped[str] = mapped_column(String(255))
    sha: Mapped[str] = mapped_column(String(255), default="")
    repository_name: Mapped[str] = mapped_column(String(255))
    repository_user: Mapped[str] = mapped_column(String(255))
    file_extension: Mapped[str] = mapped_column(String(255))
    path_in_repo: Mapped[str] = mapped_column(String(255))
    latest_version: Mapped[bool]
    is_embedded: Mapped[bool]

    __table_args__ = (
        ForeignKeyConstraint(
            ["repository_name", "repository_user"],
            [
                "github_repositories.name",
                "github_repositories.user",
            ],
        ),
    )

    repository: Mapped[GitHubRepositoryModel] = relationship(
        back_populates="files", foreign_keys=[repository_name, repository_user]
    )
