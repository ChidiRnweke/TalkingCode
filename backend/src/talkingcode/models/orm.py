"""SQLAlchemy ORM models."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from talkingcode.enums import (
    Area,
    FileType,
    IngestionStatus,
    ToolCallStatus,
    TurnStatus,
)


class Base(DeclarativeBase):
    """Base ORM model."""
    pass


class Repository(Base):
    """Repository table."""
    
    __tablename__ = "repositories"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(50), default="github")
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(255), default="main")
    last_ingested_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("provider", "owner", "name", name="uq_repo_provider_owner_name"),
    )
    
    documents: Mapped[list["Document"]] = relationship(back_populates="repository")
    ingestion_runs: Mapped[list["IngestionRun"]] = relationship(back_populates="repository")


class Document(Base):
    """Document table."""
    
    __tablename__ = "documents"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    git_ref: Mapped[str] = mapped_column(String(255), default="main")
    content_sha: Mapped[str] = mapped_column(String(64), nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="")
    area: Mapped[str] = mapped_column(String(50), default=Area.UNKNOWN.value)
    file_type: Mapped[str] = mapped_column(String(50), default=FileType.UNKNOWN.value)
    symbols_json: Mapped[dict] = mapped_column(JSONB, default=list)
    tags_json: Mapped[dict] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "path", "git_ref", name="uq_document_repo_path_ref"
        ),
        Index("idx_document_repo_path", "repository_id", "path"),
    )
    
    repository: Mapped[Repository] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")


class DocumentChunk(Base):
    """Document chunk table."""
    
    __tablename__ = "document_chunks"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(default=0)
    language: Mapped[str] = mapped_column(String(50), default="")
    area: Mapped[str] = mapped_column(String(50), default=Area.UNKNOWN.value)
    file_type: Mapped[str] = mapped_column(String(50), default=FileType.UNKNOWN.value)
    symbols_json: Mapped[dict] = mapped_column(JSONB, default=list)
    tags_json: Mapped[dict] = mapped_column(JSONB, default=list)
    start_line: Mapped[int | None] = mapped_column(nullable=True)
    end_line: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_index"),
        Index("idx_chunk_area_type", "area", "file_type"),
        Index("idx_chunk_symbols", "symbols_json", postgresql_using="gin"),
        Index("idx_chunk_tags", "tags_json", postgresql_using="gin"),
    )
    
    document: Mapped[Document] = relationship(back_populates="chunks")
    embedding: Mapped["ChunkEmbedding | None"] = relationship(back_populates="chunk")


class ChunkEmbedding(Base):
    """Chunk embedding table (pgVector)."""
    
    __tablename__ = "chunk_embeddings"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    chunk_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("document_chunks.id"), unique=True, nullable=False
    )
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    chunk: Mapped[DocumentChunk] = relationship(back_populates="embedding")


class IngestionRun(Base):
    """Ingestion run tracking."""
    
    __tablename__ = "ingestion_runs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    repository_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default=IngestionStatus.RUNNING.value
    )
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    repository: Mapped[Repository] = relationship(back_populates="ingestion_runs")


class ConversationTurn(Base):
    """Conversation turn table."""
    
    __tablename__ = "conversation_turns"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    selected_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    planner_model_used: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default=TurnStatus.DONE.value
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    
    __table_args__ = (
        Index("idx_turn_conv_created", "conversation_id", "created_at"),
    )
    
    timeline_items: Mapped[list["ToolCallTimeline"]] = relationship(back_populates="turn")


class ToolCallTimeline(Base):
    """Tool call timeline table."""
    
    __tablename__ = "tool_call_timeline"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    turn_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("conversation_turns.id"), nullable=False
    )
    sequence_no: Mapped[int] = mapped_column(nullable=False)
    group_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    visible_args_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(
        String(20), default=ToolCallStatus.STARTED.value
    )
    success: Mapped[bool | None] = mapped_column(nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_timeline_turn_seq", "turn_id", "sequence_no"),
    )
    
    turn: Mapped[ConversationTurn] = relationship(back_populates="timeline_items")
