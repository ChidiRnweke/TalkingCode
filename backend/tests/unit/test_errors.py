"""Tests for errors."""
from talkingcode.errors import (
    TalkingCodeError,
    ValidationError,
    NotFoundError,
    ToolError,
)


class TestTalkingCodeError:
    def test_basic_error(self):
        error = TalkingCodeError("Test error")
        assert error.message == "Test error"
        assert error.code == "unknown_error"

    def test_with_code(self):
        error = TalkingCodeError("Not found", code="not_found")
        assert error.code == "not_found"


class TestValidationError:
    def test_creation(self):
        error = ValidationError("Invalid input")
        assert error.code == "validation_error"
        assert error.message == "Invalid input"


class TestNotFoundError:
    def test_creation(self):
        error = NotFoundError("User not found", resource_type="User")
        assert error.code == "not_found"
        assert error.details["resource_type"] == "User"


class TestToolError:
    def test_creation(self):
        error = ToolError("Tool failed", tool_name="retriever")
        assert error.code == "tool_error"
        assert error.details["tool_name"] == "retriever"
