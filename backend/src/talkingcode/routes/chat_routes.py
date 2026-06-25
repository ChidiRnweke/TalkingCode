"""Chat routes with SSE streaming."""

import json
from typing import Any, AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from talkingcode.config import AppConfig
from talkingcode.dependencies import get_config, get_db_session
from talkingcode.domain.models import WhiteboxEvent
from talkingcode.factory import AppFactory
from talkingcode.models.api import (
    ChatAgenticRequest,
    ToolCallInfoResponse,
    ToolTimelineResponse,
)

router = APIRouter()


def _format_sse_event(event: WhiteboxEvent) -> str:
    """Format WhiteboxEvent as SSE."""
    data: dict[str, Any] = {
        "turn_id": event.turn_id,
        "timestamp": event.timestamp.isoformat(),
    }

    if event.tool_name:
        data["tool_name"] = event.tool_name

    if event.call_id:
        data["call_id"] = event.call_id

    if event.iteration is not None:
        data["iteration"] = event.iteration

    if event.index is not None:
        data["index"] = event.index

    if event.code:
        data["code"] = event.code

    if event.visible_args:
        data["visible_args"] = event.visible_args

    if event.message:
        data["message"] = event.message

    return f"event: {event.kind.value}\ndata: {json.dumps(data)}\n\n"


@router.post("/agentic")
async def chat_agentic(
    request: ChatAgenticRequest,
    session: AsyncSession = Depends(get_db_session),
    config: AppConfig = Depends(get_config),
) -> StreamingResponse:
    """Agentic chat endpoint with SSE streaming."""
    conversation_id = request.conversation_id
    if conversation_id:
        conversation_id = UUID(conversation_id)

    question = request.question
    selected_model = request.selected_model

    factory = AppFactory(session=session, config=config)
    controller = await factory.get_chat_controller()

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
) -> ToolTimelineResponse:
    """Get chat timeline for conversation."""
    factory = AppFactory(session=session, config=config)
    controller = await factory.get_chat_controller()

    timeline = await controller.get_timeline(conversation_id)

    return ToolTimelineResponse(
        conversation_id=str(conversation_id),
        timeline=[
            ToolCallInfoResponse(
                turn_id=item.turn_id,
                tool_name=item.tool_name,
                visible_args=item.visible_args,
                status=item.status,
                duration_ms=item.duration_ms,
                timestamp=item.timestamp.isoformat(),
            )
            for item in timeline
        ],
    )
