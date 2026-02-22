"""Chat routes with SSE streaming."""
import json
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.config import AppConfig
from talkingcode.dependencies import get_config, get_db_session
from talkingcode.domain.models import WhiteboxEvent
from talkingcode.factory import AppFactory

router = APIRouter()


def _format_sse_event(event: WhiteboxEvent) -> str:
    """Format WhiteboxEvent as SSE."""
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
    
    return f"event: {event.kind.value}\ndata: {json.dumps(data)}\n\n"


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
    
    factory = AppFactory(session=session, config=config)
    controller = factory.get_chat_controller()
    
    async def event_generator() -> AsyncGenerator[str, None]:
        async for event in controller.start_agentic_turn(
            conversation_id=conversation_id,
            question=question,
            selected_model=selected_model,
        ):
            yield _format_sse_event(event)
    
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
