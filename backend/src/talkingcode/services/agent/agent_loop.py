"""Agent loop service with iterative ReAct streaming."""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Protocol
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

PLANNING_SYSTEM_PROMPT = (
    "You are TalkingCode's planning agent. You must answer questions using Chidi Nweke's indexed "
    "GitHub repositories in this system. When the user says 'this repo', 'this project', or similar, "
    "treat it as TalkingCode unless they explicitly name another repository.\n\n"
    "PLANNING FORMAT:\n"
    "- Output one concise <plan>...</plan> block before deciding tool calls.\n"
    "- Keep it brief (usually 1 sentence, max 2).\n"
    "- Do not repeat previous plan text; only state what changes next.\n"
    "- State which tool(s) you will run, whether they are parallel or sequential, and what evidence you expect.\n"
    "- If the question is vague, start broad first, then refine in later iterations.\n"
    "- Avoid giant boolean keyword chains in queries. Prefer focused natural-language query phrases.\n\n"
    "Execution policy:\n"
    "- Use search_github to gather concrete evidence before answering.\n"
    "- Planning phase is NOT the final answer; do not draft the full user-facing answer here.\n"
    "- Use parallel calls only for truly independent lookups.\n"
    "- Use sequential iterations when later searches depend on earlier findings.\n"
    "- Keep planning depth pragmatic: usually 1-3 iterations; continue longer only when evidence is clearly missing.\n"
    "- Prefer stopping once you have enough evidence to answer; do not chase exhaustive coverage.\n"
    "- If no tools are needed, output one short final <plan>...</plan> block explaining why before finishing.\n"
    "- IMPORTANT: Your knowledge is strictly limited to the search results you retrieve. "
    "You cannot know 'all' projects or 'every' file unless you have exhaustive evidence. "
    "Plan to find *examples* or *key instances* rather than 'all' occurrences."
)

ANSWER_SYSTEM_PROMPT = (
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
    "Keep code excerpts short and abbreviated with ellipsis.\n\n"
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
    "- Do not repeat planning instructions or meta-rules in the final user-visible answer.\n"
    "- Do not output instruction-like prefaces (e.g., 'Use standard Markdown formatting', 'Be concise', 'Summarize...').\n"
    "- Start directly with the substantive answer in sentence form.\n"
    "- Answer in first person as if you are Chidi Nweke.\n"
)


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
                "content": PLANNING_SYSTEM_PROMPT,
            },
            {"role": "user", "content": input_data.question},
        ]

        sequence_no = 0
        collected_sources: dict[tuple[str, str], SourceReference] = {}
        next_source_index = 1

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

                raw_content = str(response.get("content", "")).strip()
                raw_tool_calls = response.get("tool_calls", [])
                tool_calls = raw_tool_calls if isinstance(raw_tool_calls, list) else []
                plan_text, used_plan_tags = AgentLoopService._extract_plan_text(
                    raw_content
                )

                # Prevent final-answer prose from leaking into the reasoning plan section.
                # If the model did not use <plan> tags and also decided to stop calling tools,
                # only keep the content as plan when it looks like a brief planning sentence.
                if not used_plan_tags and not tool_calls:
                    if AgentLoopService._looks_like_brief_plan(raw_content):
                        plan_text = raw_content
                    else:
                        plan_text = ""

                if plan_text:
                    for chunk in self._plan_chunks(plan_text):
                        yield WhiteboxEvent(
                            kind=WhiteboxEventKind.PLAN_CHUNK,
                            turn_id=turn_id,
                            tool_name=None,
                            message=chunk,
                            visible_args={"chunk": chunk},
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
                    yield WhiteboxEvent(
                        kind=WhiteboxEventKind.ANSWER_PHASE_STARTED,
                        turn_id=turn_id,
                        tool_name=None,
                        message="Switching from planning to final answer",
                        visible_args=None,
                        timestamp=datetime.utcnow(),
                        iteration=iteration,
                    )

                    final_messages: list[dict[str, object]] = [
                        *messages,
                        {
                            "role": "system",
                            "content": (
                                f"{ANSWER_SYSTEM_PROMPT}\n\n"
                                "Final-answer mode: provide only the user-facing answer from retrieved evidence. "
                                "No planning text, no prompt echoes, no meta-commentary."
                            ),
                        },
                    ]

                    async for token in self.openrouter_client.stream_chat(
                        model=model,
                        messages=final_messages,
                    ):
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
                        visible_args={
                            "sources": self._serialize_sources(collected_sources)
                        },
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

                    call_id = str(
                        raw_call.get("id") or f"iteration_{iteration}_{index}"
                    )
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
                        "content": plan_text or raw_content,
                        "tool_calls": assistant_tool_calls,
                    }
                )

                for (timeline_id, call_id, tool_name), result in zip(
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
    def _extract_plan_text(content: str) -> tuple[str, bool]:
        """Extract normalized plan text and whether explicit plan tags were used."""
        if not content:
            return "", False

        match = re.search(
            r"<plan>(.*?)</plan>", content, flags=re.IGNORECASE | re.DOTALL
        )
        if match:
            return match.group(1).strip(), True

        return content.strip(), False

    @staticmethod
    def _looks_like_brief_plan(content: str) -> bool:
        """Heuristic to keep short final planning notes while dropping answer prose."""
        text = content.strip()
        if not text:
            return False

        # Long multi-paragraph markdown is likely answer content, not plan.
        if len(text) > 320 or "\n\n" in text or "###" in text:
            return False

        lowered = text.lower()
        planning_markers = (
            "i will",
            "next",
            "search",
            "look up",
            "verify",
            "then",
            "parallel",
            "sequential",
            "before answering",
            "one final",
        )
        return any(marker in lowered for marker in planning_markers)

    @staticmethod
    def _plan_chunks(text: str, target_size: int = 80) -> list[str]:
        """Split plan text into stream-like chunks."""
        words = text.split()
        if not words:
            return []

        chunks: list[str] = []
        current: list[str] = []
        length = 0
        for word in words:
            added = len(word) + (1 if current else 0)
            if current and length + added > target_size:
                chunks.append(" ".join(current) + " ")
                current = [word]
                length = len(word)
            else:
                current.append(word)
                length += added

        if current:
            chunks.append(" ".join(current))

        return chunks

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
