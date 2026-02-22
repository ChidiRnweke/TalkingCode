"""Agent loop service with streaming."""

from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Protocol
from uuid import UUID

import structlog
from talkingcode.domain.models import (
    AgentTurnInput,
    ExecuteToolGroupInput,
    PlannerInput,
    WhiteboxEvent,
)
from talkingcode.enums import WhiteboxEventKind
from talkingcode.services.agent.timeline_repository import TimelineRepository
from talkingcode.services.llm.openrouter_client import IOpenRouterClient
from talkingcode.services.planner.planner_service import PlannerService
from talkingcode.services.tools.tool_registry import ToolRegistry

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


class IAgentLoopService(Protocol):
    """Protocol for agent loop service."""

    async def run_turn(
        self, input_data: AgentTurnInput
    ) -> AsyncGenerator[WhiteboxEvent, None]:
        """Run an agentic conversation turn with streaming events."""
        ...


@dataclass(slots=True)
class AgentLoopService:
    """Agent loop with planner and tool execution."""

    planner: PlannerService
    openrouter_client: IOpenRouterClient
    tool_registry: ToolRegistry
    timeline_repository: TimelineRepository
    default_model: str
    max_iterations: int = 8
    max_tools_per_turn: int = 3
    default_tool_timeout: int = 15

    async def run_turn(
        self,
        input_data: AgentTurnInput,
    ) -> AsyncGenerator[WhiteboxEvent, None]:
        """Run agent turn with streaming events."""
        turn_uuid = input_data.turn_id
        turn_id = str(turn_uuid)

        # Emit planner started
        yield WhiteboxEvent(
            kind=WhiteboxEventKind.PLANNER_STARTED,
            turn_id=turn_id,
            tool_name=None,
            message="Planner started",
            visible_args=None,
            timestamp=datetime.utcnow(),
        )

        try:
            # Get plan from planner
            planner_input = PlannerInput(
                question=input_data.question,
                conversation_id=input_data.conversation_id,
                selected_model=input_data.selected_model,
            )
            plan = await self.planner.plan(planner_input)

            # Emit planner ready
            yield WhiteboxEvent(
                kind=WhiteboxEventKind.PLANNER_READY,
                turn_id=turn_id,
                tool_name=None,
                message=f"Intent: {plan.intent}",
                visible_args={
                    "intent": plan.intent,
                    "filters": {
                        "areas": [a.value for a in plan.filters.areas],
                        "languages": plan.filters.languages,
                        "file_types": [ft.value for ft in plan.filters.file_types],
                    },
                },
                timestamp=datetime.utcnow(),
            )

            # Execute tool groups
            tool_count = 0
            sequence_no = 0
            tool_results_payloads: list[str] = []
            for group in plan.tool_groups[: self.max_tools_per_turn]:
                if tool_count >= self.max_tools_per_turn:
                    break

                # Create timeline entries for each tool
                timeline_ids = []
                for call in group.calls:
                    if tool_count >= self.max_tools_per_turn:
                        break

                    visible_args = {
                        k: v
                        for k, v in call.arguments.items()
                        if k not in ["content", "payload", "data"]
                    }

                    # Persist timeline entry
                    timeline_id = await self.timeline_repository.create_timeline_entry(
                        turn_id=UUID(turn_id),
                        sequence_no=sequence_no,
                        group_name=group.name,
                        tool_name=call.tool_name,
                        visible_args=visible_args,
                    )
                    timeline_ids.append((timeline_id, call))
                    sequence_no += 1

                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.TOOL_CALL_STARTED,
                        turn_id=turn_id,
                        tool_name=call.tool_name,
                        message=f"Starting {call.tool_name}",
                        visible_args=visible_args,
                        timestamp=datetime.utcnow(),
                    )
                    tool_count += 1

                # Execute group
                group_input = ExecuteToolGroupInput(
                    group_name=group.name,
                    calls=[
                        {
                            "tool_name": c.tool_name,
                            "arguments": c.arguments,
                            "non_blocking": c.non_blocking,
                        }
                        for _, c in timeline_ids
                    ],
                    parallel=group.parallel,
                    timeout_seconds=self.default_tool_timeout,
                )

                results = await self.tool_registry.execute_group(group_input)
                tool_results_payloads.extend(
                    [
                        f"tool={result.tool_name} success={result.success} payload={result.payload_json}"
                        for result in results
                    ]
                )

                # Emit tool call finished and update timeline
                for (timeline_id, call), result in zip(timeline_ids, results):
                    await self.timeline_repository.complete_timeline_entry(
                        entry_id=timeline_id,
                        success=result.success,
                        duration_ms=result.duration_ms,
                        error_code=result.error[:50] if result.error else None,
                        error_message=result.error,
                    )

                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.TOOL_CALL_FINISHED,
                        turn_id=turn_id,
                        tool_name=result.tool_name,
                        message=f"Completed {result.tool_name}",
                        visible_args={
                            "success": result.success,
                            "duration_ms": result.duration_ms,
                        },
                        timestamp=datetime.utcnow(),
                    )

            context_lines = tool_results_payloads[: self.max_tools_per_turn]
            context_blob = "\n".join(context_lines)
            assistant_prompt = (
                f"Question:\n{input_data.question}\n\n"
                f"Planner intent: {plan.intent}\n"
                f"Tool results:\n{context_blob}"
            )

            model = input_data.selected_model or self.default_model
            async for token in self.openrouter_client.stream_chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are TalkingCode. Answer the user using the tool outputs. "
                            "Be concise and cite uncertainty when data is insufficient."
                        ),
                    },
                    {"role": "user", "content": assistant_prompt},
                ],
            ):
                yield WhiteboxEvent(
                    kind=WhiteboxEventKind.ASSISTANT_TOKEN,
                    turn_id=turn_id,
                    tool_name=None,
                    message=token,
                    visible_args=None,
                    timestamp=datetime.utcnow(),
                )

            # Emit done
            yield WhiteboxEvent(
                kind=WhiteboxEventKind.ASSISTANT_DONE,
                turn_id=turn_id,
                tool_name=None,
                message="Turn complete",
                visible_args=None,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error("Agent turn failed", error=str(e))
            yield WhiteboxEvent(
                kind=WhiteboxEventKind.AGENT_ERROR,
                turn_id=turn_id,
                tool_name=None,
                message=str(e),
                visible_args={"code": "agent_error"},
                timestamp=datetime.utcnow(),
            )
