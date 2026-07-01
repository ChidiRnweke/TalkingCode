from datetime import datetime
from uuid import uuid4

import pytest

from talkingcode.controllers.chat_controller import ChatController
from talkingcode.domain.models import AgentTurn, ChatStreamEvent
from talkingcode.enums import TurnStatus


class FakeConversationRepo:
    def __init__(self):
        self.completed_status = None

    async def create_turn(self, **kwargs):
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
    async def run_turn(self, **kwargs):
        yield ChatStreamEvent(event="markdown.delta", data={"text": "hello"})


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
