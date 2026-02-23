"""Conversation repository."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.domain.models import AgentTurn
from talkingcode.enums import TurnStatus
from talkingcode.models.orm import ConversationTurn


@dataclass(slots=True)
class ConversationRepository:
    """Repository for conversation operations."""
    
    session: AsyncSession
    
    async def create_turn(
        self,
        conversation_id: UUID | None,
        question: str,
        selected_model: str | None,
        planner_model_used: str,
    ) -> AgentTurn:
        """Create a new conversation turn."""
        turn = ConversationTurn(
            id=uuid4(),
            conversation_id=conversation_id,
            question=question,
            selected_model=selected_model,
            planner_model_used=planner_model_used,
            status=TurnStatus.DONE.value,
            created_at=datetime.utcnow(),
        )
        
        self.session.add(turn)
        await self.session.flush()
        
        return self._to_domain(turn)
    
    async def complete_turn(
        self,
        turn_id: UUID,
        status: TurnStatus = TurnStatus.DONE,
    ) -> None:
        """Mark turn as complete."""
        result = await self.session.execute(
            select(ConversationTurn).where(ConversationTurn.id == turn_id)
        )
        turn = result.scalar_one_or_none()
        
        if turn:
            turn.status = status.value
            turn.completed_at = datetime.utcnow()
            await self.session.flush()
    
    async def get_turn(self, turn_id: UUID) -> AgentTurn | None:
        """Get turn by ID."""
        result = await self.session.execute(
            select(ConversationTurn).where(ConversationTurn.id == turn_id)
        )
        turn = result.scalar_one_or_none()
        
        return self._to_domain(turn) if turn else None
    
    def _to_domain(self, turn: ConversationTurn) -> AgentTurn:
        """Convert ORM to domain model."""
        return AgentTurn(
            id=turn.id,
            conversation_id=turn.conversation_id,
            question=turn.question,
            selected_model=turn.selected_model,
            planner_model_used=turn.planner_model_used,
            status=turn.status,
            created_at=turn.created_at,
            completed_at=turn.completed_at,
        )
