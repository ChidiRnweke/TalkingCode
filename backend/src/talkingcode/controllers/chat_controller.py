"""Chat controller with SSE streaming."""
import json
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.config import AppConfig
from talkingcode.dependencies import get_config, get_db_session
from talkingcode.domain.models import AgentTurnInput, ToolTimelineItem, WhiteboxEvent
from talkingcode.domain.services import AgentTurnInput as AgentTurnInputDTO
from talkingcode.enums import WhiteboxEventKind
from talkingcode.repository.conversation_repository import ConversationRepository
from talkingcode.services.agent.agent_loop import AgentLoopService
from talkingcode.services.agent.timeline_repository import TimelineRepository

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

router = APIRouter()


@dataclass(slots=True)
class ChatController:
    """Chat controller for agentic chat."""
    
    agent_service: AgentLoopService
    timeline_repository: TimelineRepository
    conversation_repository: ConversationRepository
    config: AppConfig
    
    async def start_agentic_turn(
        self,
        conversation_id: UUID | None,
        question: str,
        selected_model: str | None,
    ) -> AsyncGenerator[WhiteboxEvent, None]:
        """Start agentic turn and stream events."""
        input_data = AgentTurnInputDTO(
            conversation_id=conversation_id,
            question=question,
            selected_model=selected_model,
        )
        
        async for event in self.agent_service.run_turn(input_data):
            yield event
    
    async def get_timeline(
        self,
        conversation_id: UUID,
    ) -> list[ToolTimelineItem]:
        """Get timeline for conversation."""
        # Get latest turn for conversation
        # For now, return empty list
        return []


@router.post("/agentic")
async def chat_agentic(
    request: dict,
    session: AsyncSession = Depends(get_db_session),
    config: AppConfig = Depends(get_config),
) -> StreamingResponse:
    """Agentic chat endpoint with SSE streaming."""
    conversation_id = request.get("conversation_id")
    if conversation_id:
        conversation_id = UUID(conversation_id)
    
    question = request.get("question", "")
    selected_model = request.get("selected_model")
    
    # Create controller
    from talkingcode.factory import AppFactory
    factory = AppFactory(session=session, config=config)
    controller = factory.get_chat_controller()
    
    async def event_generator():
        async for event in controller.start_agentic_turn(
            conversation_id=conversation_id,
            question=question,
            selected_model=selected_model,
        ):
            # Convert to SSE format
            data = {
                "turn_id": event.turn_id,
                "timestamp": event.timestamp.isoformat(),
            }
            
            if event.tool_name:
                data["tool_name"] = event.tool_name
            
            if event.visible_args:
                data["visible_args"] = event.visible_args
            
            if event.message:
                data["message"] = event.message
            
            yield f"event: {event.kind.value}\ndata: {json.dumps(data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.get("/timeline")
async def get_chat_timeline(
    conversation_id: UUID = Query(...),
    session: AsyncSession = Depends(get_db_session),
    config: AppConfig = Depends(get_config),
) -> dict:
    """Get chat timeline for conversation."""
    from talkingcode.factory import AppFactory
    factory = AppFactory(session=session, config=config)
    controller = factory.get_chat_controller()
    
    timeline = await controller.get_timeline(conversation_id)
    
    return {
        "conversation_id": str(conversation_id),
        "timeline": [
            {
                "turn_id": item.turn_id,
                "tool_name": item.tool_name,
                "visible_args": item.visible_args,
                "status": item.status,
                "duration_ms": item.duration_ms,
                "timestamp": item.timestamp.isoformat(),
            }
            for item in timeline
        ],
    }
