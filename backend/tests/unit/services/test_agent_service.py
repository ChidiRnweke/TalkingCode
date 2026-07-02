from datetime import datetime
from uuid import uuid4

import pytest
from agents import Agent, Runner
from agents.extensions.memory import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine
from agents.items import ReasoningItem, ToolCallItem, ToolCallOutputItem
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseReasoningItem,
    ResponseReasoningTextDeltaEvent,
    ResponseTextDeltaEvent,
)
from openai.types.responses.response_reasoning_item import Content

from talkingcode.domain.models import AgentTurn
from talkingcode.services.agent.agent_service import ChatAgentService, _TurnStreamState


@pytest.fixture
def service() -> ChatAgentService:
    return ChatAgentService(
        tools=[],
        openrouter_api_key="test-key",
        max_iterations=16,
        # Engines connect lazily; the stubbed Runner never touches the DB.
        engine=create_async_engine("postgresql+asyncpg://unused:unused@localhost:1/unused"),
    )


@pytest.fixture
def agent() -> Agent:
    return Agent(name="test")


def text_delta(delta: str) -> RawResponsesStreamEvent:
    return RawResponsesStreamEvent(
        data=ResponseTextDeltaEvent(
            content_index=0,
            delta=delta,
            item_id="item-1",
            logprobs=[],
            output_index=0,
            sequence_number=0,
            type="response.output_text.delta",
        )
    )


def reasoning_delta(delta: str) -> RawResponsesStreamEvent:
    return RawResponsesStreamEvent(
        data=ResponseReasoningTextDeltaEvent(
            content_index=0,
            delta=delta,
            item_id="item-1",
            output_index=0,
            sequence_number=0,
            type="response.reasoning_text.delta",
        )
    )


def reasoning_item(agent: Agent, text: str) -> RunItemStreamEvent:
    return RunItemStreamEvent(
        name="reasoning_item_created",
        item=ReasoningItem(
            agent=agent,
            raw_item=ResponseReasoningItem(
                id="reasoning-1",
                summary=[],
                content=[Content(text=text, type="reasoning_text")],
                type="reasoning",
            ),
        ),
    )


async def collect(service: ChatAgentService, event: object, state: _TurnStreamState):
    return [item async for item in service._map_agent_event(event, state)]


@pytest.mark.asyncio
async def test_text_delta_maps_to_markdown_delta(service: ChatAgentService):
    events = await collect(service, text_delta("Hello"), _TurnStreamState())

    assert events[0].event == "markdown.delta"
    assert events[0].data["text"] == "Hello"


@pytest.mark.asyncio
async def test_reasoning_delta_maps_to_reasoning_tag(service: ChatAgentService):
    events = await collect(service, reasoning_delta("checking <repo>"), _TurnStreamState())

    assert events[0].data["text"] == "<tc-reasoning>checking &lt;repo&gt;</tc-reasoning>"


@pytest.mark.asyncio
async def test_reasoning_item_suppressed_after_streamed_deltas(
    service: ChatAgentService, agent: Agent
):
    state = _TurnStreamState()
    await collect(service, reasoning_delta("checking"), state)

    events = await collect(service, reasoning_item(agent, "checking"), state)

    assert events == []
    assert state.reasoning_streamed is False


@pytest.mark.asyncio
async def test_reasoning_item_emitted_when_no_deltas_streamed(
    service: ChatAgentService, agent: Agent
):
    events = await collect(service, reasoning_item(agent, "checking"), _TurnStreamState())

    assert events[0].data["text"] == "<tc-reasoning>checking</tc-reasoning>"


@pytest.mark.asyncio
async def test_tool_called_maps_to_running_tag_with_args(
    service: ChatAgentService, agent: Agent
):
    event = RunItemStreamEvent(
        name="tool_called",
        item=ToolCallItem(
            agent=agent,
            raw_item=ResponseFunctionToolCall(
                arguments='{"query": "auth"}',
                call_id="call-1",
                name="search_github",
                type="function_call",
            ),
        ),
    )

    events = await collect(service, event, _TurnStreamState())

    text = events[0].data["text"]
    assert 'name="search_github"' in text
    assert 'call-id="call-1"' in text
    assert 'status="running"' in text
    assert "args=" in text
    assert "&quot;query&quot;" in text


@pytest.mark.asyncio
async def test_run_streamed_receives_no_conversation_id_and_configured_max_turns(
    service: ChatAgentService, monkeypatch: pytest.MonkeyPatch
):
    captured_kwargs: dict = {}

    class FakeResult:
        async def stream_events(self):
            return
            yield

    def fake_run_streamed(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return FakeResult()

    monkeypatch.setattr(Runner, "run_streamed", fake_run_streamed)
    turn = AgentTurn(
        id=uuid4(),
        conversation_id=uuid4(),
        question="What projects use Python?",
        selected_model=None,
        planner_model_used="test-model",
        status="running",
        created_at=datetime.utcnow(),
    )

    events = [
        event
        async for event in service.run_turn(
            turn=turn,
            question=turn.question,
            model_name="test-model",
        )
    ]

    assert captured_kwargs.get("conversation_id") is None
    assert captured_kwargs["max_turns"] == 16
    session = captured_kwargs["session"]
    assert isinstance(session, SQLAlchemySession)
    assert session.session_id == str(turn.conversation_id)
    assert events[-1].event == "turn.done"
    assert events[-1].data["conversation_id"] == str(turn.conversation_id)


@pytest.mark.asyncio
async def test_tool_output_maps_to_done_tag(service: ChatAgentService, agent: Agent):
    event = RunItemStreamEvent(
        name="tool_output",
        item=ToolCallOutputItem(
            agent=agent,
            raw_item={
                "call_id": "call-1",
                "output": "results",
                "type": "function_call_output",
            },
            output="results",
        ),
    )

    events = await collect(service, event, _TurnStreamState())

    text = events[0].data["text"]
    assert 'call-id="call-1"' in text
    assert 'status="done"' in text
