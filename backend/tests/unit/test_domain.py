"""Tests for domain models."""
from uuid import uuid4

from talkingcode.domain.models import (
    AgentTurnInput,
    ToolExecutionResult,
)


def test_agent_turn_input_question_is_stored() -> None:
    input_data = AgentTurnInput(
        turn_id=uuid4(),
        conversation_id=None,
        question="What is this?",
        selected_model="test-model",
    )
    assert input_data.question == "What is this?"


def test_agent_turn_input_selected_model_is_stored() -> None:
    input_data = AgentTurnInput(
        turn_id=uuid4(),
        conversation_id=None,
        question="What is this?",
        selected_model="test-model",
    )
    assert input_data.selected_model == "test-model"


def test_tool_execution_result_success_flag_is_true() -> None:
    result = ToolExecutionResult(
        call_id="123",
        tool_name="test",
        success=True,
        payload_json="{}",
        duration_ms=100,
    )
    assert result.success is True


def test_tool_execution_result_success_duration_is_preserved() -> None:
    result = ToolExecutionResult(
        call_id="123",
        tool_name="test",
        success=True,
        payload_json="{}",
        duration_ms=100,
    )
    assert result.duration_ms == 100


def test_tool_execution_result_failure_flag_is_false() -> None:
    result = ToolExecutionResult(
        call_id="123",
        tool_name="test",
        success=False,
        payload_json="{}",
        duration_ms=50,
        error="Something went wrong",
    )
    assert result.success is False


def test_tool_execution_result_failure_error_is_preserved() -> None:
    result = ToolExecutionResult(
        call_id="123",
        tool_name="test",
        success=False,
        payload_json="{}",
        duration_ms=50,
        error="Something went wrong",
    )
    assert result.error == "Something went wrong"
