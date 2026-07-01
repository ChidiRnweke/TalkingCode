"""Tests for enums."""
from talkingcode.enums import (
    Area,
    FileType,
    TurnStatus,
)


class TestArea:
    def test_values(self):
        assert Area.BACKEND.value == "backend"
        assert Area.FRONTEND.value == "frontend"
        assert Area.INFRA.value == "infra"
        assert Area.SCRIPTS.value == "scripts"
        assert Area.DOCS.value == "docs"
        assert Area.TESTS.value == "tests"
        assert Area.UNKNOWN.value == "unknown"


class TestFileType:
    def test_values(self):
        assert FileType.SOURCE.value == "source"
        assert FileType.CONFIG.value == "config"
        assert FileType.UNKNOWN.value == "unknown"


class TestTurnStatus:
    def test_values(self):
        assert TurnStatus.DONE.value == "done"
        assert TurnStatus.ERROR.value == "error"
