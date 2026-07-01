"""Chat controller."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import UUID

from talkingcode.domain.models import ChatStreamEvent
from talkingcode.enums import TurnStatus
from talkingcode.repository.conversation_repository import IConversationRepository
from talkingcode.services.agent.agent_service import IChatAgentService

@dataclass(slots=True)
class ChatController:
    """Chat controller for agentic chat orchestration."""

    agent_service: IChatAgentService
    conversation_repository: IConversationRepository
    default_model: str

    async def start_agentic_turn(
        self,
        conversation_id: UUID | None,
        question: str,
        selected_model: str | None,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """Start an agentic turn and stream events."""
        model_name = selected_model or self.default_model
        turn = await self.conversation_repository.create_turn(
            conversation_id=conversation_id,
            question=question,
            selected_model=selected_model,
            planner_model_used=model_name,
        )
        async for event in self.agent_service.run_turn(
            turn=turn,
            question=question,
            model_name=model_name,
        ):
            yield event
        await self.conversation_repository.complete_turn(turn.id, status=TurnStatus.DONE)
