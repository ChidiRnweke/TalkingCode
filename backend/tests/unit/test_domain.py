"""Tests for domain models."""
from uuid import uuid4

from talkingcode.domain.models import (
    RetrievalFilters,
    StopRules,
    PlannedToolCall,
    ToolGroupPlan,
    PlannerOutput,
    ToolExecutionResult,
)
from talkingcode.domain.services import (
    AgentTurnInput,
)
from talkingcode.enums import Area, FileType


class TestRetrievalFilters:
    def test_default_empty(self):
        filters = RetrievalFilters()
        assert filters.areas == []
        assert filters.languages == []
        assert filters.file_types == []

    def test_with_values(self):
        filters = RetrievalFilters(
            areas=[Area.BACKEND],
            languages=["python"],
            file_types=[FileType.SOURCE],
        )
        assert len(filters.areas) == 1
        assert filters.areas[0] == Area.BACKEND


class TestStopRules:
    def test_defaults(self):
        rules = StopRules()
        assert rules.max_iterations == 8
        assert rules.max_tools_per_turn == 3

    def test_custom_values(self):
        rules = StopRules(max_iterations=5, max_tools_per_turn=2)
        assert rules.max_iterations == 5
        assert rules.max_tools_per_turn == 2


class TestPlannedToolCall:
    def test_creation(self):
        call = PlannedToolCall(
            tool_name="search_github",
            arguments={"query": "test"},
        )
        assert call.tool_name == "search_github"
        assert call.arguments["query"] == "test"
        assert call.non_blocking is False


class TestToolGroupPlan:
    def test_creation(self):
        call = PlannedToolCall(tool_name="test", arguments={})
        group = ToolGroupPlan(name="group1", calls=[call], parallel=True)
        assert group.name == "group1"
        assert len(group.calls) == 1
        assert group.parallel is True


class TestPlannerOutput:
    def test_creation(self):
        filters = RetrievalFilters()
        output = PlannerOutput(
            intent="search for code",
            filters=filters,
            tool_groups=[],
        )
        assert output.intent == "search for code"
        assert output.stop_rules.max_iterations == 8


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
