"""Agent loop service with iterative ReAct streaming."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Protocol
from uuid import UUID

import structlog

from talkingcode.domain.models import AgentTurnInput, ExecuteToolGroupInput, WhiteboxEvent
from talkingcode.enums import WhiteboxEventKind
from talkingcode.services.agent.timeline_repository import TimelineRepository
from talkingcode.services.llm.openrouter_client import IOpenRouterClient
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
    """Iterative ReAct loop with parallel tool execution."""

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
        """Run one conversation turn using an iterative tool loop."""
        turn_id = str(input_data.turn_id)
        model = input_data.selected_model or self.default_model

        messages: list[dict[str, object]] = [
            {
                "role": "system",
                "content": (
                    "You are TalkingCode in an iterative ReAct tool loop. For each step, explain the next "
                    "plan briefly in plain text. Use tool calls when needed, and after tool results are "
                    "provided, continue iterating until you can answer the user directly."
                ),
            },
            {"role": "user", "content": input_data.question},
        ]

        sequence_no = 0

        try:
            for iteration in range(1, self.max_iterations + 1):
                yield WhiteboxEvent(
                    kind=WhiteboxEventKind.ITERATION_STARTED,
                    turn_id=turn_id,
                    tool_name=None,
                    message=f"Iteration {iteration}",
                    visible_args={"iteration": iteration},
                    timestamp=datetime.utcnow(),
                    iteration=iteration,
                )

                response = await self.openrouter_client.send_chat_with_tools(
                    model=model,
                    messages=messages,
                    tools=self.tool_registry.get_tool_definitions(),
                )

                plan_text = str(response.get("content", "")).strip()
                raw_tool_calls = response.get("tool_calls", [])
                tool_calls = raw_tool_calls if isinstance(raw_tool_calls, list) else []

                if plan_text:
                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.PLAN_CHUNK,
                        turn_id=turn_id,
                        tool_name=None,
                        message=plan_text,
                        visible_args={"chunk": plan_text},
                        timestamp=datetime.utcnow(),
                        iteration=iteration,
                    )
                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.PLAN_DONE,
                        turn_id=turn_id,
                        tool_name=None,
                        message=plan_text,
                        visible_args={"plan_text": plan_text},
                        timestamp=datetime.utcnow(),
                        iteration=iteration,
                    )

                if not tool_calls:
                    for token in self._to_tokens(plan_text):
                        yield WhiteboxEvent(
                            kind=WhiteboxEventKind.ASSISTANT_TOKEN,
                            turn_id=turn_id,
                            tool_name=None,
                            message=token,
                            visible_args=None,
                            timestamp=datetime.utcnow(),
                        )

                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.ASSISTANT_DONE,
                        turn_id=turn_id,
                        tool_name=None,
                        message="Turn complete",
                        visible_args=None,
                        timestamp=datetime.utcnow(),
                    )
                    return

                execution_calls: list[dict[str, object]] = []
                assistant_tool_calls: list[dict[str, object]] = []
                timeline_entries: list[tuple[UUID, str, str]] = []

                for index, raw_call in enumerate(tool_calls[: self.max_tools_per_turn]):
                    if not isinstance(raw_call, dict):
                        continue

                    tool_name = str(raw_call.get("name", "")).strip()
                    if not tool_name:
                        continue

                    call_id = str(raw_call.get("id") or f"iteration_{iteration}_{index}")
                    arguments_raw = raw_call.get("arguments", {})
                    arguments = arguments_raw if isinstance(arguments_raw, dict) else {}

                    visible_args = {
                        key: value
                        for key, value in arguments.items()
                        if key not in ["content", "payload", "data"]
                    }

                    timeline_id = await self.timeline_repository.create_timeline_entry(
                        turn_id=UUID(turn_id),
                        sequence_no=sequence_no,
                        group_name=f"iteration_{iteration}",
                        tool_name=tool_name,
                        visible_args={
                            **visible_args,
                            "call_id": call_id,
                            "iteration": iteration,
                        },
                    )
                    sequence_no += 1

                    timeline_entries.append((timeline_id, call_id, tool_name))
                    execution_calls.append(
                        {
                            "call_id": call_id,
                            "tool_name": tool_name,
                            "arguments": arguments,
                        }
                    )
                    assistant_tool_calls.append(
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments),
                            },
                        }
                    )

                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.TOOL_CALL_STARTED,
                        turn_id=turn_id,
                        tool_name=tool_name,
                        message=f"Starting {tool_name}",
                        visible_args=visible_args,
                        timestamp=datetime.utcnow(),
                        iteration=iteration,
                        call_id=call_id,
                    )

                if not execution_calls:
                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.AGENT_ERROR,
                        turn_id=turn_id,
                        tool_name=None,
                        message="Model returned malformed tool calls",
                        visible_args={"code": "malformed_model_output"},
                        timestamp=datetime.utcnow(),
                        iteration=iteration,
                        code="malformed_model_output",
                    )
                    return

                results = await self.tool_registry.execute_group(
                    ExecuteToolGroupInput(
                        group_name=f"iteration_{iteration}",
                        calls=execution_calls,
                        parallel=len(execution_calls) > 1,
                        timeout_seconds=self.default_tool_timeout,
                    )
                )

                messages.append(
                    {
                        "role": "assistant",
                        "content": plan_text,
                        "tool_calls": assistant_tool_calls,
                    }
                )

                for (timeline_id, call_id, tool_name), result in zip(timeline_entries, results):
                    await self.timeline_repository.complete_timeline_entry(
                        entry_id=timeline_id,
                        success=result.success,
                        duration_ms=result.duration_ms,
                        error_code=result.error_code,
                        error_message=result.error,
                    )

                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.TOOL_CALL_FINISHED,
                        turn_id=turn_id,
                        tool_name=tool_name,
                        message=f"Completed {tool_name}",
                        visible_args={
                            "success": result.success,
                            "duration_ms": result.duration_ms,
                            "error_code": result.error_code,
                        },
                        timestamp=datetime.utcnow(),
                        iteration=iteration,
                        call_id=call_id,
                    )

                    observation = result.payload_json
                    if not result.success:
                        observation = json.dumps(
                            {
                                "error": result.error,
                                "error_code": result.error_code,
                            }
                        )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": call_id,
                            "name": tool_name,
                            "content": observation,
                        }
                    )

            yield WhiteboxEvent(
                kind=WhiteboxEventKind.AGENT_ERROR,
                turn_id=turn_id,
                tool_name=None,
                message="Max iterations reached",
                visible_args={"code": "iteration_limit_reached"},
                timestamp=datetime.utcnow(),
                code="iteration_limit_reached",
            )

        except Exception as exc:  # noqa: BLE001
            logger.error("Agent turn failed", error=str(exc))
            yield WhiteboxEvent(
                kind=WhiteboxEventKind.AGENT_ERROR,
                turn_id=turn_id,
                tool_name=None,
                message=str(exc),
                visible_args={"code": "agent_error"},
                timestamp=datetime.utcnow(),
                code="agent_error",
            )

    @staticmethod
    def _to_tokens(text: str) -> list[str]:
        """Split text into lightweight stream-like tokens."""
        if not text:
            return []

        parts = text.split(" ")
        if len(parts) == 1:
            return parts
        return [f"{part} " for part in parts[:-1]] + [parts[-1]]
