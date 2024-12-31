from sqlalchemy import ForeignKeyConstraint, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
    pass


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
