"""Structured single-turn agent execution for evals.

Runs the production agent (same prompt, tools, and model wiring) without
session memory or SSE mapping, and captures the tool-call trajectory that the
deterministic scorers and the LLM trajectory judge evaluate.
"""

import json
import time
from typing import Any

from agents import Runner
from agents.items import ToolCallItem, ToolCallOutputItem
from agents.stream_events import RunItemStreamEvent

from talkingcode.services.agent.agent_service import (
    ChatAgentService,
    tool_call_arguments,
)

_FALLBACK_SUMMARY_CHARS = 500


def _summarize_tool_output(name: str, output: Any) -> Any:
    """Condense a tool output for experiment storage and judge prompts."""
    match name, output:
        case _, {"error": error}:
            return {"error": str(error)}
        case "search_github", {"items": [*items]}:
            return {
                "refined_query": output.get("refined_query", ""),
                "paths": [
                    f"{item.get('repository', '')}: {item.get('path', '')}"
                    for item in items
                    if isinstance(item, dict)
                ],
            }
        case "read_file", {"repository": repository, "file_path": file_path}:
            return {
                "path": f"{repository}: {file_path}",
                "chunk_count": output.get("chunk_count", 0),
            }
        case _:
            text = (
                output if isinstance(output, str) else json.dumps(output, default=str)
            )
            return text[:_FALLBACK_SUMMARY_CHARS]


def _output_paths(name: str, output: Any) -> list[str]:
    """Repository file paths surfaced by a tool output."""
    match name, output:
        case "search_github", {"items": [*items]}:
            return [
                str(item.get("path", ""))
                for item in items
                if isinstance(item, dict) and item.get("path")
            ]
        case "read_file", {"file_path": file_path, "content": _}:
            return [str(file_path)]
        case _:
            return []


def _search_query(call: dict[str, Any]) -> str | None:
    if call["name"] != "search_github":
        return None
    try:
        parsed = json.loads(call["arguments"] or "{}")
    except json.JSONDecodeError:
        return None
    query = parsed.get("query") if isinstance(parsed, dict) else None
    return str(query) if query else None


async def run_agent_turn(
    agent_service: ChatAgentService,
    *,
    question: str,
    model_name: str,
) -> dict[str, Any]:
    """Run one agent turn and return the answer plus its tool trajectory."""
    started = time.perf_counter()
    tool_calls: list[dict[str, Any]] = []
    calls_by_id: dict[str, dict[str, Any]] = {}
    retrieved_paths: list[str] = []
    tool_errors: list[str] = []

    result = Runner.run_streamed(
        agent_service.build_agent(model_name),
        input=question,
        max_turns=agent_service.max_iterations,
    )
    async for event in result.stream_events():
        match event:
            case RunItemStreamEvent(name="tool_called", item=ToolCallItem() as item):
                call: dict[str, Any] = {
                    "name": item.tool_name or "",
                    "arguments": tool_call_arguments(item),
                    "output": None,
                }
                tool_calls.append(call)
                if item.call_id:
                    calls_by_id[item.call_id] = call
            case RunItemStreamEvent(
                name="tool_output", item=ToolCallOutputItem() as item
            ):
                pending = calls_by_id.get(item.call_id or "")
                if pending is None:
                    continue
                name = str(pending["name"])
                pending["output"] = _summarize_tool_output(name, item.output)
                retrieved_paths.extend(_output_paths(name, item.output))
                match item.output:
                    case {"error": error}:
                        tool_errors.append(f"{name}: {error}")
                    case _:
                        pass
            case _:
                continue

    latency_ms = int((time.perf_counter() - started) * 1000)
    return {
        "final_answer": str(result.final_output or ""),
        "tool_calls": tool_calls,
        "tool_names": [call["name"] for call in tool_calls],
        "tool_call_count": len(tool_calls),
        "search_queries": [
            query for call in tool_calls if (query := _search_query(call))
        ],
        "retrieved_paths": retrieved_paths,
        "tool_errors": tool_errors,
        "latency_ms": latency_ms,
    }
