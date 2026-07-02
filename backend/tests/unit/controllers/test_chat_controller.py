from datetime import datetime
from uuid import uuid4

import pytest

from talkingcode.controllers.chat_controller import ChatController
from talkingcode.domain.models import AgentTurn, ChatStreamEvent
from talkingcode.enums import TurnStatus


class FakeConversationRepo:
    def __init__(self):
        self.completed_status = None
        self.created_conversation_id = None

    async def create_turn(self, **kwargs):
        self.created_conversation_id = kwargs["conversation_id"]
        return AgentTurn(
            id=uuid4(),
            conversation_id=kwargs["conversation_id"],
            question=kwargs["question"],
            selected_model=kwargs["selected_model"],
            planner_model_used=kwargs["planner_model_used"],
            status=TurnStatus.DONE.value,
            created_at=datetime.utcnow(),
        )

    async def complete_turn(self, turn_id, status=TurnStatus.DONE):
        self.completed_status = status


class FakeAgentService:
    def __init__(self):
        self.received_turn = None
        self.rewind_calls = []

    async def run_turn(self, **kwargs):
        self.received_turn = kwargs["turn"]
        yield ChatStreamEvent(event="markdown.delta", data={"text": "hello"})

    async def rewind_session(self, *, conversation_id, user_message_ordinal):
        self.rewind_calls.append((conversation_id, user_message_ordinal))


@pytest.mark.asyncio
async def test_controller_completes_turn_after_streaming():
    repo = FakeConversationRepo()
    controller = ChatController(
        agent_service=FakeAgentService(),
        conversation_repository=repo,
        default_model="test-model",
    )

    async for _ in controller.start_agentic_turn(None, "question", None):
        pass

    assert repo.completed_status == TurnStatus.DONE


@pytest.mark.asyncio
async def test_controller_assigns_conversation_id_when_missing():
    repo = FakeConversationRepo()
    agent_service = FakeAgentService()
    controller = ChatController(
        agent_service=agent_service,
        conversation_repository=repo,
        default_model="test-model",
    )

    async for _ in controller.start_agentic_turn(None, "question", None):
        pass

    assert repo.created_conversation_id is not None
    assert agent_service.received_turn.conversation_id == repo.created_conversation_id


@pytest.mark.asyncio
async def test_controller_reuses_given_conversation_id():
    repo = FakeConversationRepo()
    controller = ChatController(
        agent_service=FakeAgentService(),
        conversation_repository=repo,
        default_model="test-model",
    )
    conversation_id = uuid4()

    async for _ in controller.start_agentic_turn(conversation_id, "question", None):
        pass

    assert repo.created_conversation_id == conversation_id


@pytest.mark.asyncio
async def test_controller_rewinds_session_on_retry():
    agent_service = FakeAgentService()
    controller = ChatController(
        agent_service=agent_service,
        conversation_repository=FakeConversationRepo(),
        default_model="test-model",
    )
    conversation_id = uuid4()

    async for _ in controller.start_agentic_turn(
        conversation_id, "question", None, retry_user_ordinal=2
    ):
        pass

    assert agent_service.rewind_calls == [(conversation_id, 2)]


@pytest.mark.asyncio
async def test_controller_skips_rewind_without_conversation_id():
    agent_service = FakeAgentService()
    controller = ChatController(
        agent_service=agent_service,
        conversation_repository=FakeConversationRepo(),
        default_model="test-model",
    )

    async for _ in controller.start_agentic_turn(None, "question", None, retry_user_ordinal=1):
        pass

    assert agent_service.rewind_calls == []


@pytest.mark.asyncio
async def test_controller_skips_rewind_on_normal_turn():
    agent_service = FakeAgentService()
    controller = ChatController(
        agent_service=agent_service,
        conversation_repository=FakeConversationRepo(),
        default_model="test-model",
    )

    async for _ in controller.start_agentic_turn(uuid4(), "question", None):
        pass

    assert agent_service.rewind_calls == []
