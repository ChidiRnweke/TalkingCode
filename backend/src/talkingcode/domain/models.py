"""Domain dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from talkingcode.enums import Area, FileType, IngestionStatus, WhiteboxEventKind

# =============================================================================
# Input Models
# =============================================================================


@dataclass(slots=True, frozen=True)
class AgentTurnInput:
    """Input for starting an agentic conversation turn."""

    turn_id: UUID | None
    conversation_id: UUID | None
    question: str
    selected_model: str | None = None


@dataclass(slots=True, frozen=True)
class DocumentClassificationInput:
    """Input for document classification."""

    repo: str
    path: str
    content: str


@dataclass(slots=True, frozen=True)
class RetrievedChunk:
    """Single retrieved document chunk."""

    chunk_id: UUID
    document_id: UUID
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class DocumentClassificationOutput:
    """Document classification result."""

    language: str
    area: Area
    file_type: FileType
    symbols: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class ToolExecutionResult:
    """Result of a tool execution."""

    call_id: str
    tool_name: str
    success: bool
    payload_json: str
    duration_ms: int
    error: str | None = None
    error_code: str | None = None


@dataclass(slots=True, frozen=True)
class WhiteboxEvent:
    """Streaming event for whitebox UX."""

    kind: WhiteboxEventKind
    turn_id: str
    tool_name: str | None
    message: str
    visible_args: dict[str, Any] | None
    timestamp: datetime
    iteration: int | None = None
    call_id: str | None = None
    code: str | None = None


@dataclass(slots=True, frozen=True)
class SourceReference:
    """Citation source reference."""

    index: int
    repository: str
    path: str
    start_line: int | None = None
    end_line: int | None = None
    similarity_score: float = 0.0


@dataclass(slots=True, frozen=True)
class ToolTimelineItem:
    """Tool call timeline item (redacted)."""

    turn_id: str
    tool_name: str
    visible_args: dict[str, Any]
    status: str
    duration_ms: int | None
    timestamp: datetime
    call_id: str | None = None
    iteration: int | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(slots=True, frozen=True)
class AgentTurn:
    """Conversation turn metadata."""

    id: UUID
    conversation_id: UUID | None
    question: str
    selected_model: str | None
    planner_model_used: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class ExecuteToolGroupInput:
    """Input for executing a group of tool calls."""

    group_name: str
    calls: list[dict[str, Any]]
    parallel: bool = False
    timeout_seconds: int = 15


# =============================================================================
# Ingestion Models
# =============================================================================


@dataclass(slots=True, frozen=True)
class RepositoryInfo:
    """Domain model for a tracked repository."""

    id: UUID
    provider: str
    owner: str
    name: str
    default_branch: str
    last_ingested_at: datetime | None
    created_at: datetime


@dataclass(slots=True, frozen=True)
class RepositorySummary:
    """Summary of an indexed repository."""

    repository_id: UUID
    owner: str
    name: str
    document_count: int
    languages: list[str]
    areas: list[str]
    last_ingested_at: datetime | None


@dataclass(slots=True, frozen=True)
class RegisterRepoInput:
    """Input for registering a new repository."""

    owner: str
    name: str
    default_branch: str = "main"
    provider: str = "github"


@dataclass(slots=True, frozen=True)
class IngestionRunInfo:
    """Domain model for an ingestion run."""

    id: UUID
    repository_id: UUID
    status: IngestionStatus
    started_at: datetime
    completed_at: datetime | None
    error_message: str | None


@dataclass(slots=True, frozen=True)
class StartIngestionInput:
    """Input for starting an ingestion run."""

    repository_id: UUID
    git_ref: str | None = None


@dataclass(slots=True, frozen=True)
class GitHubFileContent:
    """A single file fetched from GitHub."""

    path: str
    content: str
    sha: str


@dataclass(slots=True, frozen=True)
class GitHubRepository:
    """A GitHub repository visible to the authenticated user."""

    owner: str
    name: str
    default_branch: str
    is_fork: bool


@dataclass(slots=True, frozen=True)
class ChunkResult:
    """A single chunk produced by the chunker."""

    content: str
    chunk_index: int
    token_count: int
    start_line: int
    end_line: int
