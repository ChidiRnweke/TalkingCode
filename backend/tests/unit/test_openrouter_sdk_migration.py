"""Tests for OpenRouter SDK-backed services."""

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from talkingcode.domain.models import (
    AgentTurnInput,
    ExecuteToolGroupInput,
    PlannedToolCall,
    PlannerInput,
    PlannerOutput,
    RetrievalFilters,
    StopRules,
    ToolExecutionResult,
    ToolGroupPlan,
)
from talkingcode.enums import WhiteboxEventKind
from talkingcode.services.agent.agent_loop import AgentLoopService
from talkingcode.services.ingestion.embedder import OpenRouterEmbedder
from talkingcode.services.planner.planner_service import PlannerService


@pytest.mark.asyncio
async def test_planner_uses_fallback_model_after_retries() -> None:
    """Planner retries selected model and then falls back."""

    class _StubClient:
        def __init__(self) -> None:
            self.models: list[str] = []
            self.failures = 0

        async def send_chat(self, *, model: str, messages: list[dict], response_format: dict | None = None) -> str:
            self.models.append(model)
            if self.failures < 2:
                self.failures += 1
                raise RuntimeError("transient failure")

            return json.dumps(
                {
                    "intent": "find code",
                    "filters": {
                        "areas": [],
                        "languages": ["python"],
                        "file_types": [],
                        "path_globs": [],
                        "repo_scopes": [],
                        "symbol_hints": [],
                        "tags": [],
                    },
                    "tool_groups": [],
                    "stop_rules": {"max_iterations": 8, "max_tools_per_turn": 3},
                }
            )

        async def send_chat_with_tools(self, *, model: str, messages: list[dict], tools: list[dict]) -> dict:
            return {"content": "", "tool_calls": []}

        async def stream_chat(self, *, model: str, messages: list[dict]):
            if False:
                yield ""

        async def generate_embeddings(self, *, model: str, texts: list[str], dimensions: int | None):
            return []

    client = _StubClient()
    service = PlannerService(
        openrouter_client=client,
        default_model="anthropic/claude-3.5-sonnet",
        fallback_model="google/gemini-3-flash",
    )

    result = await service.plan(PlannerInput(question="where is auth?"))

    assert result.intent == "find code"
    assert client.models == [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-3-flash",
    ]


@pytest.mark.asyncio
async def test_agent_loop_streams_assistant_tokens() -> None:
    """Agent loop emits incremental assistant token events."""

    class _StubOpenRouterClient:
        async def send_chat(self, *, model: str, messages: list[dict], response_format: dict | None = None) -> str:
            return ""

        async def send_chat_with_tools(self, *, model: str, messages: list[dict], tools: list[dict]) -> dict:
            tool_observation_present = any(msg.get("role") == "tool" for msg in messages)
            if not tool_observation_present:
                return {
                    "content": "Planning retrieval",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "name": "search_github",
                            "arguments": {"query": "hello"},
                        }
                    ],
                }
            return {
                "content": "Hello world",
                "tool_calls": [],
            }

        async def stream_chat(self, *, model: str, messages: list[dict]):
            for token in ["Hello", " world"]:
                yield token

        async def generate_embeddings(self, *, model: str, texts: list[str], dimensions: int | None):
            return []

    class _StubToolRegistry:
        def get_tool_definitions(self) -> list[dict]:
            return [
                {
                    "type": "function",
                    "function": {
                        "name": "search_github",
                        "description": "retrieve",
                        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}},
                    },
                }
            ]

        async def execute_group(self, input_data: ExecuteToolGroupInput) -> list[ToolExecutionResult]:
            return [
                ToolExecutionResult(
                    call_id="call_1",
                    tool_name="search_github",
                    success=True,
                    payload_json='{"items": []}',
                    duration_ms=12,
                )
            ]

    class _StubTimelineRepo:
        async def create_timeline_entry(
            self,
            turn_id,
            sequence_no: int,
            group_name: str,
            tool_name: str,
            visible_args: dict,
        ):
            return uuid4()

        async def complete_timeline_entry(
            self,
            entry_id,
            success: bool,
            duration_ms: int,
            error_code: str | None = None,
            error_message: str | None = None,
        ) -> None:
            return None

    service = AgentLoopService(
        openrouter_client=_StubOpenRouterClient(),
        tool_registry=_StubToolRegistry(),
        timeline_repository=_StubTimelineRepo(),
        default_model="anthropic/claude-3.5-sonnet",
    )

    input_data = AgentTurnInput(
        turn_id=uuid4(),
        conversation_id=None,
        question="Summarize retrieval",
        selected_model=None,
    )

    events = [event async for event in service.run_turn(input_data)]

    kinds = [event.kind for event in events]
    assert WhiteboxEventKind.ITERATION_STARTED in kinds
    assert WhiteboxEventKind.PLAN_DONE in kinds
    assert WhiteboxEventKind.TOOL_CALL_STARTED in kinds
    assert WhiteboxEventKind.TOOL_CALL_FINISHED in kinds
    assert kinds.count(WhiteboxEventKind.ASSISTANT_TOKEN) >= 1
    assert kinds[-1] == WhiteboxEventKind.ASSISTANT_DONE

    tokens = [event.message for event in events if event.kind == WhiteboxEventKind.ASSISTANT_TOKEN]
    assert "".join(tokens) == "Hello world"


@pytest.mark.asyncio
async def test_embedder_uses_openrouter_embeddings_client() -> None:
    """Embedder delegates to OpenRouter client generate_embeddings."""
    client = AsyncMock()
    client.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2], [0.3, 0.4]])

    embedder = OpenRouterEmbedder(
        openrouter_client=client,
        model="openai/text-embedding-3-small",
        dimensions=1536,
    )

    vectors = await embedder.embed_batch(["a", "b"])

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    client.generate_embeddings.assert_awaited_once_with(
        model="openai/text-embedding-3-small",
        texts=["a", "b"],
        dimensions=1536,
    )
