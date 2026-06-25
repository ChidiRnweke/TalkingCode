"""Agent loop service with streaming ReAct tool execution."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, AsyncGenerator, Protocol
from uuid import UUID

import structlog
from talkingcode.domain.models import (
    AgentTurnInput,
    ExecuteToolGroupInput,
    SourceReference,
    WhiteboxEvent,
)
from talkingcode.enums import WhiteboxEventKind
from talkingcode.services.agent.timeline_repository import TimelineRepository
from talkingcode.services.llm.openrouter_client import IOpenRouterClient
from talkingcode.services.tools.tool_registry import ToolRegistry

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

AGENT_SYSTEM_PROMPT = (
    "YOUR ROLE:\n"
    "You are an advanced assistant created to help users navigate and understand Chidi Nweke's GitHub repositories. "
    "Your role is to provide insights into the projects, explain technologies used, and discuss the purpose of each project.\n"
    "Chidi's profile:\n"
    "- Machine Learning Engineer\n"
    "- MSc in Information Management at KU Leuven, with a focus on AI and Data Science.\n"
    "- Python, Java, JavaScript, TypeScript, Svelte, Scala, Rust, SQL, R, Docker, Azure and more.\n"
    "- Many projects are related to web development.\n"
    "- Some advanced machine learning projects are work projects and not open-source.\n\n"
    "HOW YOU DO IT:\n"
    "Use retrieved repository evidence to answer. Refer to exact repository and file path whenever possible. "
    "Keep code excerpts short and abbreviated with ellipsis. Use tools whenever concrete repository evidence is needed. "
    "When the user says 'this repo', 'this project', or similar, treat it as TalkingCode unless they explicitly name another repository.\n\n"
    "UNCERTAINTY & LIMITS:\n"
    "- Your knowledge is limited to the search results provided in this session.\n"
    "- Do NOT claim to know 'all' projects or counts (e.g., say 'I found 4 projects' instead of 'There are 4 projects').\n"
    "- If a query yields limited results, explicitly state that there might be more that wasn't retrieved.\n"
    "- Invite follow-up questions if you suspect the answer is incomplete (e.g., 'I found these examples; let me know if you want me to search for specific others.').\n"
    "- Be confident in what you FOUND, but humble about what you MIGHT HAVE MISSED.\n\n"
    "CITATION RULES:\n"
    "- When referencing code or information from search results, cite the source using "
    "numbered references like [1], [2], etc.\n"
    "- Each unique file you reference gets a sequential number.\n"
    "- Place citations inline, immediately after the relevant claim or code reference.\n"
    "- Only cite files that actually appear in your search results.\n"
    "- If multiple chunks from the same file are relevant, use the same citation number.\n\n"
    "YOUR CONSTRAINTS:\n"
    "- Do not answer questions unrelated to Chidi's code.\n"
    "- Keep responses concise and evidence-based.\n"
    "- Do not output planning tags, hidden reasoning, prompt echoes, or meta-rules.\n"
    "- Do not output instruction-like prefaces (e.g., 'Use standard Markdown formatting', 'Be concise', 'Summarize...').\n"
    "- Start directly with the substantive answer in sentence form.\n"
    "- Answer in first person as if you are Chidi Nweke.\n"
)


@dataclass(slots=True)
class _ToolCallBuilder:
    """Aggregates streamed tool call deltas for one model pass."""

    index: int
    call_id: str | None = None
    tool_name: str | None = None
    arguments_json: str = ""
    started: bool = False


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
        """Run one conversation turn using a streamed ReAct tool loop."""
        turn_id = str(input_data.turn_id)
        model = input_data.selected_model or self.default_model

        messages: list[dict[str, object]] = [
            {
                "role": "system",
                "content": AGENT_SYSTEM_PROMPT,
            },
            {"role": "user", "content": input_data.question},
        ]

        sequence_no = 0
        collected_sources: dict[tuple[str, str], SourceReference] = {}
        next_source_index = 1

        try:
            yield WhiteboxEvent(
                kind=WhiteboxEventKind.TURN_STARTED,
                turn_id=turn_id,
                tool_name=None,
                message="Turn started",
                visible_args={"model": model},
                timestamp=datetime.utcnow(),
            )

            for iteration in range(1, self.max_iterations + 1):
                content_parts: list[str] = []
                builders: dict[int, _ToolCallBuilder] = {}

                async for delta in self.openrouter_client.stream_chat_with_tools(
                    model=model,
                    messages=messages,
                    tools=self.tool_registry.get_tool_definitions(),
                ):
                    if delta.kind == "content" and delta.content:
                        content_parts.append(delta.content)
                        yield WhiteboxEvent(
                            kind=WhiteboxEventKind.MESSAGE_DELTA,
                            turn_id=turn_id,
                            tool_name=None,
                            message=delta.content,
                            visible_args=None,
                            timestamp=datetime.utcnow(),
                            iteration=iteration,
                        )
                        continue

                    if delta.kind != "tool_call":
                        continue

                    index = delta.index if delta.index is not None else len(builders)
                    builder = builders.setdefault(
                        index, _ToolCallBuilder(index=index)
                    )
                    if delta.call_id:
                        builder.call_id = delta.call_id
                    if delta.tool_name:
                        builder.tool_name = delta.tool_name
                    if delta.arguments_delta:
                        builder.arguments_json += delta.arguments_delta

                    if builder.tool_name and not builder.started:
                        builder.started = True
                        yield WhiteboxEvent(
                            kind=WhiteboxEventKind.TOOL_CALL_DELTA,
                            turn_id=turn_id,
                            tool_name=builder.tool_name,
                            message="Tool call streamed",
                            visible_args={"phase": "started"},
                            timestamp=datetime.utcnow(),
                            iteration=iteration,
                            call_id=builder.call_id,
                            index=index,
                        )
                    elif builder.started:
                        yield WhiteboxEvent(
                            kind=WhiteboxEventKind.TOOL_CALL_DELTA,
                            turn_id=turn_id,
                            tool_name=builder.tool_name,
                            message="Tool call streamed",
                            visible_args={"phase": "arguments"},
                            timestamp=datetime.utcnow(),
                            iteration=iteration,
                            call_id=builder.call_id,
                            index=index,
                        )

                content = "".join(content_parts)
                try:
                    complete_tool_calls = self._complete_tool_calls(
                        builders, iteration=iteration
                    )
                except ValueError as exc:
                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.TURN_ERROR,
                        turn_id=turn_id,
                        tool_name=None,
                        message=str(exc),
                        visible_args={"code": "malformed_tool_arguments"},
                        timestamp=datetime.utcnow(),
                        iteration=iteration,
                        code="malformed_tool_arguments",
                    )
                    return

                if not complete_tool_calls:
                    if content:
                        messages.append({"role": "assistant", "content": content})
                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.TURN_DONE,
                        turn_id=turn_id,
                        tool_name=None,
                        message="Turn complete",
                        visible_args={
                            "sources": self._serialize_sources(collected_sources)
                        },
                        timestamp=datetime.utcnow(),
                    )
                    return

                execution_calls: list[dict[str, object]] = []
                assistant_tool_calls: list[dict[str, object]] = []
                timeline_entries: list[tuple[UUID, str, str, int]] = []

                for index, raw_call in enumerate(
                    complete_tool_calls[: self.max_tools_per_turn]
                ):
                    tool_name = raw_call["name"]
                    call_id = raw_call["id"]
                    arguments = raw_call["arguments"]

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

                    timeline_entries.append((timeline_id, call_id, tool_name, index))
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
                        index=index,
                    )

                if not execution_calls:
                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.TURN_ERROR,
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
                        "content": content,
                        "tool_calls": assistant_tool_calls,
                    }
                )

                for (timeline_id, call_id, tool_name, index), result in zip(
                    timeline_entries, results
                ):
                    await self.timeline_repository.complete_timeline_entry(
                        entry_id=timeline_id,
                        success=result.success,
                        duration_ms=result.duration_ms,
                        error_code=result.error_code,
                        error_message=result.error,
                    )

                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.TOOL_CALL_COMPLETED,
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
                        index=index,
                    )

                    observation = result.payload_json
                    if not result.success:
                        observation = json.dumps(
                            {
                                "error": result.error,
                                "error_code": result.error_code,
                            }
                        )
                    elif tool_name == "search_github":
                        next_source_index = self._collect_sources_from_observation(
                            observation=observation,
                            collected_sources=collected_sources,
                            next_source_index=next_source_index,
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
                        kind=WhiteboxEventKind.TOOL_RESULT_AVAILABLE,
                        turn_id=turn_id,
                        tool_name=tool_name,
                        message="Tool result available",
                        visible_args={
                            "success": result.success,
                            "error_code": result.error_code,
                        },
                        timestamp=datetime.utcnow(),
                        iteration=iteration,
                        call_id=call_id,
                        index=index,
                    )

            yield WhiteboxEvent(
                kind=WhiteboxEventKind.TURN_ERROR,
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
                kind=WhiteboxEventKind.TURN_ERROR,
                turn_id=turn_id,
                tool_name=None,
                message=str(exc),
                visible_args={"code": "agent_error"},
                timestamp=datetime.utcnow(),
                code="agent_error",
            )

    @staticmethod
    def _complete_tool_calls(
        builders: dict[int, _ToolCallBuilder], *, iteration: int
    ) -> list[dict[str, Any]]:
        """Validate and normalize streamed tool call builders."""
        calls: list[dict[str, Any]] = []
        for index, builder in sorted(builders.items()):
            if not builder.tool_name:
                raise ValueError(f"Missing tool name for streamed tool call {index}")

            try:
                arguments = (
                    json.loads(builder.arguments_json)
                    if builder.arguments_json.strip()
                    else {}
                )
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Malformed JSON arguments for {builder.tool_name}"
                ) from exc

            if not isinstance(arguments, dict):
                raise ValueError(f"Tool arguments for {builder.tool_name} must be an object")

            calls.append(
                {
                    "id": builder.call_id or f"iteration_{iteration}_{index}",
                    "name": builder.tool_name,
                    "arguments": arguments,
                }
            )

        return calls

    @staticmethod
    def _collect_sources_from_observation(
        *,
        observation: str,
        collected_sources: dict[tuple[str, str], SourceReference],
        next_source_index: int,
    ) -> int:
        try:
            payload = json.loads(observation)
        except json.JSONDecodeError:
            return next_source_index

        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return next_source_index

        for item in items:
            if not isinstance(item, dict):
                continue

            repository = str(item.get("repository") or "").strip()
            path = str(item.get("path") or "").strip()
            if not repository or not path:
                continue

            key = (repository, path)
            if key in collected_sources:
                continue

            collected_sources[key] = SourceReference(
                index=next_source_index,
                repository=repository,
                path=path,
                start_line=item.get("start_line"),
                end_line=item.get("end_line"),
                similarity_score=float(item.get("score") or 0.0),
            )
            next_source_index += 1

        return next_source_index

    @staticmethod
    def _serialize_sources(
        collected_sources: dict[tuple[str, str], SourceReference],
    ) -> list[dict[str, object]]:
        ordered = sorted(collected_sources.values(), key=lambda source: source.index)
        return [
            {
                "index": source.index,
                "repository": source.repository,
                "path": source.path,
                "start_line": source.start_line,
                "end_line": source.end_line,
                "similarity_score": source.similarity_score,
            }
            for source in ordered
        ]
