"""Conversation repository."""
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.domain.models import AgentTurn
from talkingcode.enums import TurnStatus
from talkingcode.models.orm import ConversationTurn


class IConversationRepository(Protocol):
    """Protocol for conversation repository."""

    async def create_turn(
        self,
        conversation_id: UUID | None,
        question: str,
        selected_model: str | None,
        planner_model_used: str,
    ) -> AgentTurn: ...

    async def complete_turn(
        self,
        turn_id: UUID,
        status: TurnStatus = TurnStatus.DONE,
    ) -> None: ...

    async def get_turn(self, turn_id: UUID) -> AgentTurn | None: ...


@dataclass(slots=True)
class ConversationRepository:
    """Repository for conversation operations."""

    session: AsyncSession

    async def _get_turn_orm(self, turn_id: UUID) -> ConversationTurn | None:
        result = await self.session.scalars(
            select(ConversationTurn).where(ConversationTurn.id == turn_id)
        )
        return result.one_or_none()

    async def create_turn(
        self,
        conversation_id: UUID | None,
        question: str,
        selected_model: str | None,
        planner_model_used: str,
    ) -> AgentTurn:
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

        return _to_domain(turn)

    async def complete_turn(
        self,
        turn_id: UUID,
        status: TurnStatus = TurnStatus.DONE,
    ) -> None:
        turn = await self._get_turn_orm(turn_id)

        if turn:
            turn.status = status.value
            turn.completed_at = datetime.utcnow()
            await self.session.flush()

    async def get_turn(self, turn_id: UUID) -> AgentTurn | None:
        result = await self.session.scalars(
            select(ConversationTurn).where(ConversationTurn.id == turn_id)
        )
        turn = result.one_or_none()

        return _to_domain(turn) if turn else None


def _to_domain(turn: ConversationTurn) -> AgentTurn:
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
