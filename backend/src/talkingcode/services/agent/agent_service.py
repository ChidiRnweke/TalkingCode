"""OpenAI Agents SDK chat agent service."""

import html
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import structlog
from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    Tool,
)
from agents.extensions.memory import SQLAlchemySession
from agents.items import ReasoningItem, ToolCallItem, ToolCallOutputItem
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncEngine  # noqa: import-boundary:sqlalchemy-location — SDK session memory needs the engine
from openai.types.responses import (
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseReasoningTextDeltaEvent,
    ResponseTextDeltaEvent,
)
from talkingcode.domain.models import AgentTurn, ChatStreamEvent

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

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
    "HOW YOU WORK:\n"
    "- Work step by step, like a real investigation. Use tools whenever concrete repository "
    "evidence is needed; you may search several times across multiple turns. When the user says "
    "'this repo', 'this project', or similar, treat it as TalkingCode unless they explicitly name "
    "another repository.\n"
    "- Answer progressively in prose: after a search returns, write a sentence or two about what "
    "you found and what you want to check next, then search again. Keep building the answer this "
    "way across turns, and once you have enough evidence, finish with the complete answer.\n"
    "GROUNDING:\n"
    "- Use retrieved repository evidence to answer. Refer to the exact repository and file path whenever possible. "
    "Keep code excerpts short and abbreviated with an ellipsis.\n\n"
    "CITATION RULES:\n"
    "- When referencing code or information from search results, cite the source using "
    "numbered references like [1], [2], etc.\n"
    "- Each unique file you reference gets a sequential number.\n"
    "- Place citations inline, immediately after the relevant claim or code reference.\n"
    "- Only cite files that actually appear in your search results.\n\n"
    "YOUR CONSTRAINTS:\n"
    "- Do not answer questions unrelated to Chidi's code.\n"
    "- Keep the answer concise and evidence-based.\n"
    "- Answer in first person as if you are Chidi Nweke.\n"
)


class IChatAgentService(Protocol):
    """Protocol for chat agent execution."""

    def run_turn(
        self,
        *,
        turn: AgentTurn,
        question: str,
        model_name: str,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """Run an agent turn and stream markdown events."""
        ...


@dataclass(slots=True)
class _TurnStreamState:
    """Per-turn streaming state; the service itself is shared across requests."""

    reasoning_streamed: bool = False


@dataclass(slots=True)
class ChatAgentService:
    """OpenAI Agents SDK-backed agent service."""

    tools: Sequence[Tool]
    openrouter_api_key: str
    max_iterations: int
    engine: AsyncEngine

    async def run_turn(
        self,
        *,
        turn: AgentTurn,
        question: str,
        model_name: str,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """Run an agent turn and stream markdown/custom-tag events."""
        # No conversation_id: Chat Completions is stateless, and server-managed
        # conversation mode would drop the question from follow-up model calls.
        # Multi-turn memory comes from the SDK session, which replays the
        # transcript stored in agent_sessions/agent_messages.
        result = Runner.run_streamed(
            self._build_agent(model_name),
            input=question,
            max_turns=self.max_iterations,
            session=SQLAlchemySession(
                str(turn.conversation_id),
                engine=self.engine,
            ),
        )
        state = _TurnStreamState()
        async for event in result.stream_events():
            async for stream_event in self._map_agent_event(event, state):
                yield stream_event

        yield ChatStreamEvent(
            event="turn.done",
            data={
                "turn_id": str(turn.id),
                "conversation_id": str(turn.conversation_id),
                "sources": [],
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def _build_agent(self, model_name: str) -> Agent:
        client = AsyncOpenAI(
            api_key=self.openrouter_api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://talkingcode.dev",
                "X-Title": "TalkingCode",
            },
        )
        model = OpenAIChatCompletionsModel(
            model=model_name,
            openai_client=client,
        )
        return Agent(
            name="TalkingCode",
            instructions=AGENT_SYSTEM_PROMPT,
            model=model,
            tools=list(self.tools),
        )

    async def _map_agent_event(
        self,
        event: RawResponsesStreamEvent | RunItemStreamEvent | object,
        state: "_TurnStreamState",
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        match event:
            case RawResponsesStreamEvent(data=ResponseTextDeltaEvent(delta=delta)):
                yield self._markdown(delta)
            case RawResponsesStreamEvent(
                data=ResponseReasoningTextDeltaEvent(delta=delta)
                | ResponseReasoningSummaryTextDeltaEvent(delta=delta)
            ):
                state.reasoning_streamed = True
                yield self._reasoning(delta)
            case RunItemStreamEvent(name="reasoning_item_created", item=ReasoningItem() as item):
                # The completed item repeats text already sent as deltas; only
                # emit it when the provider never streamed reasoning deltas.
                if state.reasoning_streamed:
                    state.reasoning_streamed = False
                    return
                reasoning = self._reasoning_text(item)
                if reasoning:
                    yield self._reasoning(reasoning)
            case RunItemStreamEvent(name="tool_called", item=ToolCallItem() as item):
                yield self._tool_tag(
                    status="running",
                    tool_name=item.tool_name or "",
                    tool_call_id=item.call_id or "",
                    args=self._tool_args(item),
                )
            case RunItemStreamEvent(name="tool_output", item=ToolCallOutputItem() as item):
                yield self._tool_tag(
                    status="done",
                    tool_name="",
                    tool_call_id=item.call_id or "",
                )
            case _:
                return

    def _tool_tag(
        self,
        *,
        status: str,
        tool_name: str,
        tool_call_id: str,
        args: str = "",
    ) -> ChatStreamEvent:
        attrs = {
            "name": tool_name,
            "call-id": tool_call_id,
            "status": status,
            "args": args,
        }
        rendered_attrs = " ".join(
            f'{key}="{html.escape(value, quote=True)}"'
            for key, value in attrs.items()
            if value
        )
        return self._markdown(f"<tc-tool {rendered_attrs}></tc-tool>")

    @staticmethod
    def _tool_args(item: ToolCallItem) -> str:
        """Return the raw JSON arguments of a tool call, if available."""
        if isinstance(item.raw_item, dict):
            return item.raw_item.get("arguments") or ""
        return getattr(item.raw_item, "arguments", None) or ""

    @staticmethod
    def _reasoning(text: str) -> ChatStreamEvent:
        return ChatAgentService._markdown(
            f"<tc-reasoning>{html.escape(text)}</tc-reasoning>"
        )

    @staticmethod
    def _reasoning_text(item: ReasoningItem) -> str:
        if item.raw_item.content:
            return "\n".join(part.text for part in item.raw_item.content if part.text)
        if item.raw_item.summary:
            return "\n".join(part.text for part in item.raw_item.summary if part.text)
        return ""

    @staticmethod
    def _markdown(text: str) -> ChatStreamEvent:
        return ChatStreamEvent(
            event="markdown.delta",
            data={"text": text, "timestamp": datetime.utcnow().isoformat()},
        )
