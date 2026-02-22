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
    PLANNER_STARTED = "planner_started"
    PLANNER_READY = "planner_ready"
    TOOL_CALL_STARTED = "tool_call_started"
    TOOL_CALL_FINISHED = "tool_call_finished"
    ASSISTANT_TOKEN = "assistant_token"
    ASSISTANT_DONE = "assistant_done"
    AGENT_ERROR = "agent_error"
