"""Enum definitions."""
from enum import Enum


class Area(str, Enum):
    """Code area classification."""
    BACKEND = "backend"
    FRONTEND = "frontend"
    INFRA = "infra"
    SCRIPTS = "scripts"
    DOCS = "docs"
    TESTS = "tests"
    UNKNOWN = "unknown"


class FileType(str, Enum):
    """File type classification."""
    SOURCE = "source"
    CONFIG = "config"
    MIGRATION = "migration"
    TEST = "test"
    DOCS = "docs"
    CI = "ci"
    UNKNOWN = "unknown"


class IngestionStatus(str, Enum):
    """Ingestion run status."""
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class TurnStatus(str, Enum):
    """Conversation turn status."""
    DONE = "done"
    ERROR = "error"


class ToolCallStatus(str, Enum):
    """Tool call timeline status."""
    STARTED = "started"
    FINISHED = "finished"
    FAILED = "failed"


class WhiteboxEventKind(str, Enum):
    """Whitebox streaming event types."""
    TURN_STARTED = "turn.started"
    MESSAGE_DELTA = "message.delta"
    REASONING_DELTA = "reasoning.delta"
    STEP_SUMMARY = "step.summary"
    TOOL_CALL_STARTED = "tool_call.started"
    TOOL_CALL_DELTA = "tool_call.delta"
    TOOL_CALL_COMPLETED = "tool_call.completed"
    TOOL_RESULT_AVAILABLE = "tool_result.available"
    TURN_DONE = "turn.done"
    TURN_ERROR = "turn.error"
