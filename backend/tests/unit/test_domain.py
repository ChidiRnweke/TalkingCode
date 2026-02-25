"""Tests for domain models."""
from uuid import uuid4

from talkingcode.domain.models import (
    AgentTurnInput,
    ToolExecutionResult,
)


class TestAgentTurnInput:
    def test_creation(self):
        input_data = AgentTurnInput(
            turn_id=uuid4(),
            conversation_id=None,
            question="What is this?",
            selected_model="test-model",
        )
        assert input_data.question == "What is this?"
        assert input_data.selected_model == "test-model"


class TestToolExecutionResult:
    def test_success(self):
        result = ToolExecutionResult(
            call_id="123",
            tool_name="test",
            success=True,
            payload_json="{}",
            duration_ms=100,
        )
        assert result.success is True
        assert result.duration_ms == 100

    def test_failure(self):
        result = ToolExecutionResult(
            call_id="123",
            tool_name="test",
            success=False,
            payload_json="{}",
            duration_ms=50,
            error="Something went wrong",
        )
        assert result.success is False
        assert result.error == "Something went wrong"
