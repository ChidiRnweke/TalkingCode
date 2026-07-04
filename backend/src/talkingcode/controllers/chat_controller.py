"""Chat controller."""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import UUID, uuid4

from talkingcode.domain.models import AgentTurn, ChatStreamEvent
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
        retry_user_ordinal: int | None = None,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """Start an agentic turn and stream events."""
        model_name = selected_model or self.default_model
        await self._rewind_for_retry(conversation_id, retry_user_ordinal)
        conversation_id = conversation_id or uuid4()
        turn = await self._create_turn(conversation_id, question, selected_model, model_name)
        async for event in self._stream_turn(turn, question, model_name):
            yield event
        await self.conversation_repository.complete_turn(turn.id, status=TurnStatus.DONE)

    async def _rewind_for_retry(
        self,
        conversation_id: UUID | None,
        retry_user_ordinal: int | None,
    ) -> None:
        # A retry of the very first turn arrives without a conversation id
        # (the client only learns it on turn.done), so there is no session
        # to rewind yet.
        if retry_user_ordinal is not None and conversation_id is not None:
            await self.agent_service.rewind_session(
                conversation_id=conversation_id,
                user_message_ordinal=retry_user_ordinal,
            )

    async def _create_turn(
        self,
        conversation_id: UUID,
        question: str,
        selected_model: str | None,
        model_name: str,
    ) -> AgentTurn:
        # Server-assigned identity: the turn row, the SDK session memory, and
        # the turn.done payload must all share the same conversation id.
        return await self.conversation_repository.create_turn(
            conversation_id=conversation_id,
            question=question,
            selected_model=selected_model,
            planner_model_used=model_name,
        )

    async def _stream_turn(
        self,
        turn: AgentTurn,
        question: str,
        model_name: str,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        async for event in self.agent_service.run_turn(
            turn=turn,
            question=question,
            model_name=model_name,
        ):
            yield event
