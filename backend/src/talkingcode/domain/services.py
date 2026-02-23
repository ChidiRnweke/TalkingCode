"""Service input/output dataclasses.

DEPRECATED: These dataclasses have been moved to domain/models.py.
Import from there instead.
"""
# Re-export from models for backward compatibility during migration
from talkingcode.domain.models import (
    AgentTurnInput,
    DocumentClassificationInput,
    ExecuteToolGroupInput,
    GetFileDetailsToolInput,
    GetFileDetailsToolOutput,
    PlannerInput,
    RetrieveChunksToolInput,
    RetrieveChunksToolOutput,
)

__all__ = [
    "AgentTurnInput",
    "DocumentClassificationInput",
    "ExecuteToolGroupInput",
    "GetFileDetailsToolInput",
    "GetFileDetailsToolOutput",
    "PlannerInput",
    "RetrieveChunksToolInput",
    "RetrieveChunksToolOutput",
]
