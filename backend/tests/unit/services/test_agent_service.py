from datetime import datetime
from uuid import uuid4

import pytest
from agents import Agent, Runner
from agents.extensions.memory import SQLAlchemySession
from agents.items import ReasoningItem, ToolCallItem, ToolCallOutputItem
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseReasoningItem,
    ResponseReasoningTextDeltaEvent,
    ResponseTextDeltaEvent,
)
from openai.types.responses.response_reasoning_item import Content
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool
from talkingcode.domain.models import AgentTurn, TurnStreamState
from talkingcode.services.agent.agent_service import ChatAgentService


@pytest.fixture
def service() -> ChatAgentService:
    return ChatAgentService(
        tools=[],
        openrouter_api_key="test-key",
        max_iterations=16,
        # Engines connect lazily; the stubbed Runner never touches the DB.
        engine=create_async_engine(
            "postgresql+asyncpg://unused:unused@localhost:1/unused"
        ),
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


async def collect(service: ChatAgentService, event: object, state: TurnStreamState):
    return [item async for item in service._map_agent_event(event, state)]


@pytest.mark.asyncio
async def test_text_delta_maps_to_markdown_delta(service: ChatAgentService):
    events = await collect(service, text_delta("Hello"), TurnStreamState())

    assert events[0].event == "markdown.delta"
    assert events[0].data["text"] == "Hello"


@pytest.mark.asyncio
async def test_reasoning_delta_maps_to_reasoning_tag(service: ChatAgentService):
    events = await collect(
        service, reasoning_delta("checking <repo>"), TurnStreamState()
    )

    assert (
        events[0].data["text"] == "<tc-reasoning>checking &lt;repo&gt;</tc-reasoning>"
    )


@pytest.mark.asyncio
async def test_reasoning_item_suppressed_after_streamed_deltas(
    service: ChatAgentService, agent: Agent
):
    state = TurnStreamState()
    await collect(service, reasoning_delta("checking"), state)

    events = await collect(service, reasoning_item(agent, "checking"), state)

    assert events == []
    assert state.reasoning_streamed is False


@pytest.mark.asyncio
async def test_reasoning_item_emitted_when_no_deltas_streamed(
    service: ChatAgentService, agent: Agent
):
    events = await collect(
        service, reasoning_item(agent, "checking"), TurnStreamState()
    )

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

    events = await collect(service, event, TurnStreamState())

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


def sqlite_service() -> ChatAgentService:
    # StaticPool so every connection sees the same in-memory database;
    # production creates the agent session tables via alembic instead.
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    return ChatAgentService(
        tools=[],
        openrouter_api_key="test-key",
        max_iterations=16,
        engine=engine,
    )


async def seed_session(
    service: ChatAgentService, conversation_id, items: list[dict]
) -> None:
    session = SQLAlchemySession(
        str(conversation_id), engine=service.engine, create_tables=True
    )
    await session.add_items(items)  # type: ignore


def user_item(content: str) -> dict:
    return {"role": "user", "content": content}


def assistant_item(content: str) -> dict:
    return {
        "role": "assistant",
        "type": "message",
        "status": "completed",
        "content": [{"type": "output_text", "text": content, "annotations": []}],
    }


def tool_call_items(call_id: str) -> list[dict]:
    return [
        {
            "type": "function_call",
            "call_id": call_id,
            "name": "search_github",
            "arguments": "{}",
        },
        {"type": "function_call_output", "call_id": call_id, "output": "results"},
    ]


@pytest.mark.asyncio
async def test_rewind_session_drops_nth_user_message_and_everything_after():
    service = sqlite_service()
    conversation_id = uuid4()
    turn_one = [user_item("q1"), *tool_call_items("call-1"), assistant_item("a1")]
    turn_two = [user_item("q2"), assistant_item("a2")]
    await seed_session(service, conversation_id, turn_one + turn_two)

    await service.rewind_session(
        conversation_id=conversation_id, user_message_ordinal=2
    )

    assert await service._session(conversation_id).get_items() == turn_one


@pytest.mark.asyncio
async def test_rewind_session_at_first_user_message_empties_session():
    service = sqlite_service()
    conversation_id = uuid4()
    await seed_session(
        service, conversation_id, [user_item("q1"), assistant_item("a1")]
    )

    await service.rewind_session(
        conversation_id=conversation_id, user_message_ordinal=1
    )

    assert await service._session(conversation_id).get_items() == []


@pytest.mark.asyncio
async def test_rewind_session_noop_when_ordinal_exceeds_user_messages():
    service = sqlite_service()
    conversation_id = uuid4()
    items = [user_item("q1"), assistant_item("a1")]
    await seed_session(service, conversation_id, items)

    await service.rewind_session(
        conversation_id=conversation_id, user_message_ordinal=2
    )

    assert await service._session(conversation_id).get_items() == items


@pytest.mark.asyncio
async def test_rewind_session_noop_on_missing_session():
    service = sqlite_service()
    other_conversation = uuid4()
    items = [user_item("q1")]
    await seed_session(service, other_conversation, items)

    await service.rewind_session(conversation_id=uuid4(), user_message_ordinal=1)

    assert await service._session(other_conversation).get_items() == items


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

    events = await collect(service, event, TurnStreamState())

    text = events[0].data["text"]
    assert 'call-id="call-1"' in text
    assert 'status="done"' in text
