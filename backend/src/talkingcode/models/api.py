"""Shared API request/response schemas for FastAPI routes."""

from typing import Any

from pydantic import BaseModel, Field


class RegisterRepoRequest(BaseModel):
    """Request body for registering a repository."""

    owner: str
    name: str
    default_branch: str = "main"


class StartIngestionRequest(BaseModel):
    """Request body for starting an ingestion run."""

    git_ref: str | None = None


class ModelInfoResponse(BaseModel):
    """Information about a chat model."""

    id: str
    label: str


class ModelListResponse(BaseModel):
    """Response model for model list endpoint."""

    models: list[ModelInfoResponse]
    default: str


class ChatAgenticRequest(BaseModel):
    """Request payload for agentic chat endpoint."""

    conversation_id: str | None = None
    question: str = ""
    selected_model: str | None = None


class ToolCallInfoResponse(BaseModel):
    """Information about a tool call in the timeline."""

    turn_id: str
    tool_name: str
    visible_args: dict[str, Any] = Field(default_factory=dict)
    status: str
    duration_ms: int | None
    timestamp: str


class ToolTimelineResponse(BaseModel):
    """Response model for tool timeline endpoint."""

    conversation_id: str
    timeline: list[ToolCallInfoResponse]
