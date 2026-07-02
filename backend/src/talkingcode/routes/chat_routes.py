"""Chat routes with SSE streaming."""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from talkingcode.dependencies import FactoryDep
from talkingcode.models.api import ChatAgenticRequest

router = APIRouter()


async def _sse_event_stream(
    controller,
    conversation_id: UUID | None,
    question: str,
    selected_model: str | None,
    retry_user_ordinal: int | None,
) -> AsyncGenerator[str, None]:
    async for event in controller.start_agentic_turn(
        conversation_id=conversation_id,
        question=question,
        selected_model=selected_model,
        retry_user_ordinal=retry_user_ordinal,
    ):
        yield event.to_sse()


@router.post("/agentic")
async def chat_agentic(request: ChatAgenticRequest, factory: FactoryDep) -> StreamingResponse:
    """Agentic chat endpoint with SSE streaming."""
    controller = await factory.get_chat_controller()
    cid = UUID(request.conversation_id) if request.conversation_id else None
    stream = _sse_event_stream(
        controller,
        cid,
        request.question,
        request.selected_model,
        request.retry_user_ordinal,
    )
    return StreamingResponse(stream, media_type="text/event-stream")

