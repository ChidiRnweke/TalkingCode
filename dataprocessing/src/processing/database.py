from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (
    Column,
    ForeignKeyConstraint,
    String,
    Integer,
    ForeignKey,
    Table,
)
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class LanguagesModel(Base):
    __tablename__ = "github_languages"

    language: Mapped[str] = mapped_column(String(255), primary_key=True)


languages_repository_bridge = Table(
    "languages_repository_bridge",
    Base.metadata,
    Column("language_name", ForeignKey("github_languages.language")),
    Column("repository_name", String(255)),
    Column("repository_user", String(255)),
    ForeignKeyConstraint(
        ["repository_name", "repository_user"],
        ["github_repositories.name", "github_repositories.user"],
    ),
)


class GitHubRepositoryModel(Base):
    __tablename__ = "github_repositories"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    user: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    url: Mapped[str] = mapped_column(String(255))

    files: Mapped[list["GithubFileModel"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    languages: Mapped[list[LanguagesModel]] = relationship(
        secondary=languages_repository_bridge
    )


class GithubFileModel(Base):
    __tablename__ = "github_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    content_url: Mapped[str] = mapped_column(String(255))
    last_modified: Mapped[datetime]
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


class EmbeddedDocumentModel(Base):
    __tablename__ = "embedded_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("github_files.id"))
    embedding: Mapped[Vector] = mapped_column(Vector(3072))

    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id"],
            ["github_files.id"],
        ),
    )

    document: Mapped[GithubFileModel] = relationship(
        back_populates="embeddings", foreign_keys=[document_id]
    )
