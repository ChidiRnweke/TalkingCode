"""Service input/output dataclasses."""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from talkingcode.domain.models import RetrievalFilters


# Planner Service

@dataclass(slots=True, frozen=True)
class PlannerInput:
    """Input to planner service."""
    question: str
    conversation_id: UUID | None = None
    selected_model: str | None = None


# Classification Service

@dataclass(slots=True, frozen=True)
class DocumentClassificationInput:
    """Input to document classifier."""
    repo: str
    path: str
    content: str


# Tool Service

@dataclass(slots=True, frozen=True)
class RetrieveChunksToolInput:
    """Input to retrieve chunks tool."""
    query: str
    filters: RetrievalFilters
    top_k: int = 10


@dataclass(slots=True, frozen=True)
class RetrieveChunksToolOutput:
    """Output from retrieve chunks tool."""
    items: list[dict[str, Any]]
    total: int


@dataclass(slots=True, frozen=True)
class GetFileDetailsToolInput:
    """Input to get file details tool."""
    repo: str
    path: str
    ref: str | None = None


@dataclass(slots=True, frozen=True)
class GetFileDetailsToolOutput:
    """Output from get file details tool."""
    repo: str
    path: str
    summary: str
    symbols: list[str]


# Agent Service

@dataclass(slots=True, frozen=True)
class AgentTurnInput:
    """Input to agent loop service."""
    question: str
    conversation_id: UUID | None = None
    selected_model: str | None = None


@dataclass(slots=True, frozen=True)
class ExecuteToolGroupInput:
    """Input to tool executor."""
    group_name: str
    calls: list[dict[str, Any]]
    parallel: bool = False
    timeout_seconds: int = 15
