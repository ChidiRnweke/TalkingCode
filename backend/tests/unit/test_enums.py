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
        assert WhiteboxEventKind.TURN_STARTED.value == "turn.started"
        assert WhiteboxEventKind.MESSAGE_DELTA.value == "message.delta"
        assert WhiteboxEventKind.TOOL_CALL_STARTED.value == "tool_call.started"
        assert WhiteboxEventKind.TOOL_CALL_DELTA.value == "tool_call.delta"
        assert WhiteboxEventKind.TOOL_CALL_COMPLETED.value == "tool_call.completed"
        assert WhiteboxEventKind.TOOL_RESULT_AVAILABLE.value == "tool_result.available"
        assert WhiteboxEventKind.TURN_DONE.value == "turn.done"
        assert WhiteboxEventKind.TURN_ERROR.value == "turn.error"
