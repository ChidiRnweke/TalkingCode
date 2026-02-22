"""Domain dataclasses."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from talkingcode.enums import Area, FileType, WhiteboxEventKind


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


@dataclass(slots=True, frozen=True)
class WhiteboxEvent:
    """Streaming event for whitebox UX."""
    kind: WhiteboxEventKind
    turn_id: str
    tool_name: str | None
    message: str
    visible_args: dict[str, Any] | None
    timestamp: datetime


@dataclass(slots=True, frozen=True)
class ToolTimelineItem:
    """Tool call timeline item (redacted)."""
    turn_id: str
    tool_name: str
    visible_args: dict[str, Any]
    status: str
    duration_ms: int | None
    timestamp: datetime
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
