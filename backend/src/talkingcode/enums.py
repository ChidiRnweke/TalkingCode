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

