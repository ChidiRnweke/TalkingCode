"""Timeline repository."""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.domain.models import ToolTimelineItem
from talkingcode.enums import ToolCallStatus
from talkingcode.models.orm import ToolCallTimeline


@dataclass(slots=True)
class TimelineRepository:
    """Repository for tool call timeline."""
    
    session: AsyncSession
    
    async def create_timeline_entry(
        self,
        turn_id: UUID,
        sequence_no: int,
        group_name: str,
        tool_name: str,
        visible_args: dict,
    ) -> UUID:
        """Create timeline entry."""
        from uuid import uuid4
        
        entry = ToolCallTimeline(
            id=uuid4(),
            turn_id=turn_id,
            sequence_no=sequence_no,
            group_name=group_name,
            tool_name=tool_name,
            visible_args_json=visible_args,
            status=ToolCallStatus.STARTED.value,
            created_at=datetime.utcnow(),
        )
        
        self.session.add(entry)
        await self.session.flush()
        
        return entry.id
    
    async def complete_timeline_entry(
        self,
        entry_id: UUID,
        success: bool,
        duration_ms: int,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Mark timeline entry as complete."""
        result = await self.session.execute(
            select(ToolCallTimeline).where(ToolCallTimeline.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        
        if entry:
            entry.status = ToolCallStatus.FINISHED.value if success else ToolCallStatus.FAILED.value
            entry.success = success
            entry.duration_ms = duration_ms
            entry.error_code = error_code
            entry.error_message = error_message
            await self.session.flush()
    
    async def get_timeline_for_turn(
        self,
        turn_id: UUID,
    ) -> list[ToolTimelineItem]:
        """Get timeline for a turn."""
        result = await self.session.execute(
            select(ToolCallTimeline)
            .where(ToolCallTimeline.turn_id == turn_id)
            .order_by(ToolCallTimeline.sequence_no)
        )
        entries = result.scalars().all()
        
        return [self._to_domain(entry) for entry in entries]
    
    def _to_domain(self, entry: ToolCallTimeline) -> ToolTimelineItem:
        """Convert ORM to domain model."""
        return ToolTimelineItem(
            turn_id=str(entry.turn_id),
            tool_name=entry.tool_name,
            visible_args=entry.visible_args_json,
            status=entry.status,
            duration_ms=entry.duration_ms,
            timestamp=entry.created_at,
            error_code=entry.error_code,
            error_message=entry.error_message,
        )
