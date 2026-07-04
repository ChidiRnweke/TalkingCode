"""LLM trajectory judge: was the agent's tool path headed the right way?

Follows the Arize trace-level eval pattern: the judge reads the ordered tool
calls (with arguments), not the final answer, and labels the decision path.
Runs through OpenRouter with the existing AsyncOpenAI dependency.
"""

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

from openai import AsyncOpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

LABEL_SCORES = {"on_track": 1.0, "wandering": 0.5, "lost": 0.0}

AVAILABLE_TOOLS = (
    "search_github(query): semantic search across indexed GitHub repositories. "
    "The primary evidence-gathering tool.\n"
    "get_project_descriptions(query): names and descriptions of indexed projects. "
    "For questions about which projects exist.\n"
    "read_file(repository, file_path): read a specific file surfaced by a search."
)

JUDGE_PROMPT = """You are evaluating the DECISION PATH of a code-navigation agent \
that answers questions about Chidi Nweke's GitHub repositories. You are NOT \
judging the final answer text - only whether the agent's tool choices were \
sensible, non-redundant, and converging toward the question.

The agent has these tools available:
{available_tools}

##
User question:
{question}

Decision path (ordered tool calls with arguments and condensed results):
{tool_path}
##

Label the decision path with exactly one of:
- "on_track": tool choices fit the question, queries are focused and \
non-redundant, and each call builds on what came before.
- "wandering": the agent got there (or close) but with redundant, unfocused, \
or off-topic calls along the way.
- "lost": tool choices do not fit the question, queries chase the wrong \
topic, or the agent never gathered the evidence the question needs.

Respond with JSON only: {{"label": "<on_track|wandering|lost>", "explanation": "<one or two sentences>"}}"""


def parse_judgement(text: str) -> tuple[str, str]:
    """Best-effort extraction of (label, explanation) from a judge response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            label = str(parsed.get("label", "")).strip().lower()
            if label in LABEL_SCORES:
                return label, str(parsed.get("explanation", ""))
        except json.JSONDecodeError:
            pass
    lowered = text.lower()
    for label in LABEL_SCORES:
        if label in lowered:
            return label, text.strip()
    raise ValueError(f"judge response has no recognizable label: {text[:200]}")


def _format_tool_path(output: Any) -> str:
    calls = output.get("tool_calls", []) if isinstance(output, dict) else []
    if not calls:
        return "No tools called"
    lines = []
    for index, call in enumerate(calls, start=1):
        result = json.dumps(call.get("output"), default=str)
        lines.append(f"{index}. {call['name']}({call['arguments']}) -> {result}")
    return "\n".join(lines)


def make_trajectory_judge(
    *,
    api_key: str,
    model: str,
) -> Callable[..., Awaitable[dict[str, Any]]]:
    """Build an async experiment evaluator that judges the tool trajectory."""
    client = AsyncOpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)

    async def trajectory_judge(output: Any, input: dict[str, Any]) -> dict[str, Any]:
        prompt = JUDGE_PROMPT.format(
            available_tools=AVAILABLE_TOOLS,
            question=input.get("question", ""),
            tool_path=_format_tool_path(output),
        )
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        text = response.choices[0].message.content or ""
        label, explanation = parse_judgement(text)
        return {
            "score": LABEL_SCORES[label],
            "label": label,
            "explanation": explanation,
        }

    return trajectory_judge
