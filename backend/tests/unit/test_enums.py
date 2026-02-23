"""Tests for enums."""
from talkingcode.enums import (
    Area,
    FileType,
    TurnStatus,
    WhiteboxEventKind,
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


class TestWhiteboxEventKind:
    def test_values(self):
        assert WhiteboxEventKind.ITERATION_STARTED.value == "iteration_started"
        assert WhiteboxEventKind.PLAN_DONE.value == "plan_done"
        assert WhiteboxEventKind.TOOL_CALL_STARTED.value == "tool_call_started"
        assert WhiteboxEventKind.ASSISTANT_DONE.value == "assistant_done"
