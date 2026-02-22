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
class PlannerInput:
    """Input for the planner service."""
    question: str
    conversation_id: UUID | None = None
    selected_model: str | None = None


@dataclass(slots=True, frozen=True)
class DocumentClassificationInput:
    """Input for document classification."""
    repo: str
    path: str
    content: str


@dataclass(slots=True, frozen=True)
class ToolExecutionRequest:
    """Request to execute a tool."""
    call_id: str
    tool_name: str
    arguments: dict[str, Any]


# =============================================================================
# Core Models
# =============================================================================

@dataclass(slots=True, frozen=True)
class RetrievalFilters:
    """Retrieval filter parameters."""
    areas: list[Area] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    file_types: list[FileType] = field(default_factory=list)
    path_globs: list[str] = field(default_factory=list)
    repo_scopes: list[str] = field(default_factory=list)
    symbol_hints: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class StopRules:
    """Agent loop stop conditions."""
    max_iterations: int = 8
    max_tools_per_turn: int = 3


@dataclass(slots=True, frozen=True)
class PlannedToolCall:
    """Single planned tool call."""
    tool_name: str
    arguments: dict[str, Any]
    non_blocking: bool = False


@dataclass(slots=True, frozen=True)
class ToolGroupPlan:
    """Group of tool calls to execute."""
    name: str
    calls: list[PlannedToolCall]
    parallel: bool = False


@dataclass(slots=True, frozen=True)
class PlannerOutput:
    """Planner structured output."""
    intent: str
    filters: RetrievalFilters
    tool_groups: list[ToolGroupPlan]
    stop_rules: StopRules = field(default_factory=StopRules)


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


# =============================================================================
# Tool IO Models
# =============================================================================

@dataclass(slots=True, frozen=True)
class RetrieveChunksToolInput:
    """Input for the retrieve chunks tool."""
    query: str
    filters: RetrievalFilters
    top_k: int = 10


@dataclass(slots=True, frozen=True)
class RetrieveChunksToolOutput:
    """Output from the retrieve chunks tool."""
    items: list[RetrievedChunk]
    total: int


@dataclass(slots=True, frozen=True)
class GetFileDetailsToolInput:
    """Input for the get file details tool."""
    repo: str
    path: str
    ref: str | None = None


@dataclass(slots=True, frozen=True)
class GetFileDetailsToolOutput:
    """Output from the get file details tool."""
    repo: str
    path: str
    summary: str
    symbols: list[str] = field(default_factory=list)


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
