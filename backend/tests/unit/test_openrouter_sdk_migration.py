"""Tests for OpenRouter SDK-backed services."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from talkingcode.domain.models import (
    AgentTurnInput,
    ExecuteToolGroupInput,
    ToolExecutionResult,
)
from talkingcode.enums import WhiteboxEventKind
from talkingcode.services.agent.agent_loop import AgentLoopService
from talkingcode.services.ingestion.embedder import OpenRouterEmbedder
from talkingcode.services.llm.openrouter_client import ChatStreamDelta


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


@pytest.mark.asyncio
async def test_agent_loop_streams_tool_calls_and_message_deltas() -> None:
    """Agent loop emits streamed tool call and assistant message events."""

    class _StubOpenRouterClient:
        async def send_chat(self, *, model: str, messages: list[dict], response_format: dict | None = None) -> str:
            return ""

        async def send_chat_with_tools(self, *, model: str, messages: list[dict], tools: list[dict]) -> dict:
            return {"content": "", "tool_calls": []}

        async def stream_chat_with_tools(self, *, model: str, messages: list[dict], tools: list[dict]):
            tool_observation_present = any(msg.get("role") == "tool" for msg in messages)
            if not tool_observation_present:
                yield ChatStreamDelta(
                    kind="tool_call",
                    index=0,
                    call_id="call_1",
                    tool_name="search_github",
                )
                yield ChatStreamDelta(
                    kind="tool_call",
                    index=0,
                    arguments_delta='{"query":',
                )
                yield ChatStreamDelta(
                    kind="tool_call",
                    index=0,
                    arguments_delta='"hello"}',
                )
                return

            for token in ["Hello", " world"]:
                yield ChatStreamDelta(kind="content", content=token)

        async def stream_chat(self, *, model: str, messages: list[dict]):
            for token in ["Hello", " world"]:
                yield token

        async def generate_embeddings(self, *, model: str, texts: list[str], dimensions: int | None):
            return []

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
    assert WhiteboxEventKind.TURN_STARTED in kinds
    assert WhiteboxEventKind.TOOL_CALL_DELTA in kinds
    assert WhiteboxEventKind.TOOL_CALL_STARTED in kinds
    assert WhiteboxEventKind.TOOL_CALL_COMPLETED in kinds
    assert WhiteboxEventKind.TOOL_RESULT_AVAILABLE in kinds
    assert kinds.count(WhiteboxEventKind.MESSAGE_DELTA) >= 1
    assert kinds[-1] == WhiteboxEventKind.TURN_DONE

    tokens = [event.message for event in events if event.kind == WhiteboxEventKind.MESSAGE_DELTA]
    assert "".join(tokens) == "Hello world"


@pytest.mark.asyncio
async def test_agent_loop_streams_text_tool_text_in_order() -> None:
    """Content streamed around a tool call remains ordered in the event stream."""

    class _StubOpenRouterClient:
        async def send_chat(self, *, model: str, messages: list[dict], response_format: dict | None = None) -> str:
            return ""

        async def send_chat_with_tools(self, *, model: str, messages: list[dict], tools: list[dict]) -> dict:
            return {"content": "", "tool_calls": []}

        async def stream_chat_with_tools(self, *, model: str, messages: list[dict], tools: list[dict]):
            tool_observation_present = any(msg.get("role") == "tool" for msg in messages)
            if not tool_observation_present:
                yield ChatStreamDelta(kind="content", content="I'll search first. ")
                yield ChatStreamDelta(
                    kind="tool_call",
                    index=0,
                    call_id="call_1",
                    tool_name="search_github",
                )
                yield ChatStreamDelta(
                    kind="tool_call",
                    index=0,
                    arguments_delta='{"query":"hello"}',
                )
                return

            yield ChatStreamDelta(kind="content", content="Grounded answer.")

        async def stream_chat(self, *, model: str, messages: list[dict]):
            yield ""

        async def generate_embeddings(self, *, model: str, texts: list[str], dimensions: int | None):
            return []

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

    sequence = [
        event.message if event.kind == WhiteboxEventKind.MESSAGE_DELTA else event.kind.value
        for event in events
        if event.kind
        in {
            WhiteboxEventKind.MESSAGE_DELTA,
            WhiteboxEventKind.TOOL_CALL_STARTED,
            WhiteboxEventKind.TOOL_CALL_COMPLETED,
        }
    ]
    assert sequence == [
        "I'll search first. ",
        "tool_call.started",
        "tool_call.completed",
        "Grounded answer.",
    ]


@pytest.mark.asyncio
async def test_agent_loop_emits_reasoning_and_step_summary() -> None:
    """A tool step emits reasoning deltas and a single narration-derived summary."""

    class _StubOpenRouterClient:
        async def send_chat(self, *, model: str, messages: list[dict], response_format: dict | None = None) -> str:
            return ""

        async def send_chat_with_tools(self, *, model: str, messages: list[dict], tools: list[dict]) -> dict:
            return {"content": "", "tool_calls": []}

        async def stream_chat_with_tools(self, *, model: str, messages: list[dict], tools: list[dict]):
            tool_observation_present = any(msg.get("role") == "tool" for msg in messages)
            if not tool_observation_present:
                yield ChatStreamDelta(kind="reasoning", reasoning="Let me think. ")
                yield ChatStreamDelta(kind="content", content="Searching the repo.")
                yield ChatStreamDelta(
                    kind="tool_call",
                    index=0,
                    call_id="call_1",
                    tool_name="search_github",
                )
                yield ChatStreamDelta(kind="tool_call", index=0, arguments_delta='{"query":"hello"}')
                return
            yield ChatStreamDelta(kind="content", content="Grounded answer.")

        async def stream_chat(self, *, model: str, messages: list[dict]):
            yield ""

        async def generate_embeddings(self, *, model: str, texts: list[str], dimensions: int | None):
            return []

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

    assert WhiteboxEventKind.REASONING_DELTA in kinds
    reasoning_text = "".join(
        event.message for event in events if event.kind == WhiteboxEventKind.REASONING_DELTA
    )
    assert reasoning_text == "Let me think. "

    summaries = [event for event in events if event.kind == WhiteboxEventKind.STEP_SUMMARY]
    assert len(summaries) == 1
    assert summaries[0].message == "Searching the repo."
    assert summaries[0].iteration == 1

    # The summary heads its tool execution.
    assert kinds.index(WhiteboxEventKind.STEP_SUMMARY) < kinds.index(
        WhiteboxEventKind.TOOL_CALL_STARTED
    )


def test_derive_step_summary_prefers_narration_then_tool_label() -> None:
    """Summary uses the model's narration line, falling back to a tool-derived label."""
    assert AgentLoopService._derive_step_summary("First line.\nrest", []) == "First line."

    label = AgentLoopService._derive_step_summary(
        "", [{"name": "search_github", "arguments": {"query": "chat loop"}}]
    )
    assert "Searching the repositories for" in label
    assert "chat loop" in label


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
