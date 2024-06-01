from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, String, Integer, ForeignKey, Table


class Base(DeclarativeBase):
    pass


class LanguagesModel(Base):
    __tablename__ = "github_languages"

    language: Mapped[str] = mapped_column(String(255), primary_key=True)


languages_repository_bridge = Table(
    "association_table",
    Base.metadata,
    Column("language_name", ForeignKey("github_languages.name")),
    Column("repository_name", ForeignKey("github_repositories.name")),
    Column("repository_user", ForeignKey("github_repositories.user")),
)


class GitHubRepositoryModel(Base):
    __tablename__ = "github_repositories"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    user: Mapped[str] = mapped_column(String(255), primary_key=True)
    description: Mapped[str] = mapped_column(String(255))

    url: Mapped[str] = mapped_column(String(255))

    files: Mapped[list["GithubFileModel"]] = relationship(
        back_populates="repository", cascade="all, delete-orphan"
    )
    languages: Mapped[set[LanguagesModel]] = relationship(
        secondary=languages_repository_bridge
    )


class GithubFileModel(Base):
    __tablename__ = "github_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    content_url: Mapped[str] = mapped_column(String(255))
    last_modified: Mapped[datetime]
    repository_name: Mapped[str] = mapped_column(ForeignKey("github_repositories.name"))
    repository_user: Mapped[str] = mapped_column(ForeignKey("github_repositories.user"))

    repository: Mapped[GitHubRepositoryModel] = relationship(back_populates="files")
