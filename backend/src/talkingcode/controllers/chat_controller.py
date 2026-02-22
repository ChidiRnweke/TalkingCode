"""Chat controller."""
from dataclasses import dataclass
from typing import AsyncGenerator
from uuid import UUID

import structlog

from talkingcode.domain.models import AgentTurnInput, ToolTimelineItem, WhiteboxEvent
from talkingcode.enums import TurnStatus, WhiteboxEventKind
from talkingcode.repository.conversation_repository import ConversationRepository
from talkingcode.services.agent.agent_loop import AgentLoopService
from talkingcode.services.agent.timeline_repository import TimelineRepository

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True)
class ChatController:
    """Chat controller for agentic chat orchestration."""
    
    agent_service: AgentLoopService
    timeline_repository: TimelineRepository
    conversation_repository: ConversationRepository
    
    async def start_agentic_turn(
        self,
        conversation_id: UUID | None,
        question: str,
        selected_model: str | None,
    ) -> AsyncGenerator[WhiteboxEvent, None]:
        """Start agentic turn and stream events."""
        turn = await self.conversation_repository.create_turn(
            conversation_id=conversation_id,
            question=question,
            selected_model=selected_model,
            planner_model_used=selected_model or self.agent_service.default_model,
        )

        input_data = AgentTurnInput(
            turn_id=turn.id,
            conversation_id=conversation_id,
            question=question,
            selected_model=selected_model,
        )

        status = TurnStatus.DONE
        async for event in self.agent_service.run_turn(input_data):
            if event.kind == WhiteboxEventKind.AGENT_ERROR:
                status = TurnStatus.ERROR
            yield event

        await self.conversation_repository.complete_turn(turn.id, status=status)
    
    async def get_timeline(
        self,
        conversation_id: UUID,
    ) -> list[ToolTimelineItem]:
        """Get timeline for conversation (redacted, no payloads)."""
        # This would typically query by conversation_id
        # For now, return empty list as we need conversation -> turn mapping
        return []
