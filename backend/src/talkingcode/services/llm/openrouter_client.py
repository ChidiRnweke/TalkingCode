"""OpenRouter SDK adapter."""

import json
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Literal, Protocol, cast

import mlflow
from openrouter import OpenRouter
import structlog

from talkingcode.errors import InfraError

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class ChatStreamDelta:
    """Normalized streamed chat delta."""

    kind: Literal["content", "reasoning", "tool_call"]
    content: str = ""
    reasoning: str = ""
    index: int | None = None
    call_id: str | None = None
    tool_name: str | None = None
    arguments_delta: str = ""


class IOpenRouterClient(Protocol):
    """Protocol for OpenRouter SDK operations."""

    async def send_chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Send a non-streaming chat completion and return message content."""
        ...

    def stream_chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion delta content chunks."""
        ...

    def stream_chat_with_tools(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AsyncGenerator[ChatStreamDelta, None]:
        """Stream chat completion deltas, including tool call deltas."""
        ...

    async def generate_embeddings(
        self,
        *,
        model: str,
        texts: list[str],
        dimensions: int | None,
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        ...

    async def send_chat_with_tools(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Send chat request that may return tool calls."""
        ...


@dataclass(slots=True)
class OpenRouterClient:
    """OpenRouter SDK backed client."""

    api_key: str
    http_referer: str = "https://talkingcode.dev"
    x_title: str = "TalkingCode"
    timeout_ms: int = 60_000

    async def send_chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Send a non-streaming chat request."""
        try:
            with mlflow.start_span(name="openrouter_send_chat") as span:
                span.set_inputs(
                    {
                        "model": model,
                        "message_count": len(messages),
                        "response_format": response_format is not None,
                    }
                )
                async with OpenRouter(
                    api_key=self.api_key,
                    http_referer=self.http_referer,
                    x_title=self.x_title,
                    timeout_ms=self.timeout_ms,
                ) as client:
                    response = await client.chat.send_async(
                        model=model,
                        messages=cast(Any, messages),
                        response_format=cast(Any, response_format),
                    )

                content = _extract_message_content(response)
                span.set_outputs({"content_length": len(content)})
                return content
        except Exception as exc:  # noqa: BLE001
            raise InfraError(f"OpenRouter chat request failed: {exc}") from exc

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion token deltas."""
        try:
            with mlflow.start_span(name="openrouter_stream_chat") as span:
                span.set_inputs({"model": model, "message_count": len(messages)})
                token_count = 0
                content_length = 0
                async with OpenRouter(
                    api_key=self.api_key,
                    http_referer=self.http_referer,
                    x_title=self.x_title,
                    timeout_ms=self.timeout_ms,
                ) as client:
                    stream = await client.chat.send_async(
                        model=model,
                        messages=cast(Any, messages),
                        stream=True,
                    )
                    async with stream:
                        async for chunk in stream:
                            token = _extract_delta_content(chunk)
                            if token:
                                token_count += 1
                                content_length += len(token)
                                yield token

                span.set_outputs(
                    {
                        "token_count": token_count,
                        "content_length": content_length,
                    }
                )
        except Exception as exc:  # noqa: BLE001
            raise InfraError(f"OpenRouter streaming request failed: {exc}") from exc

    async def stream_chat_with_tools(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AsyncGenerator[ChatStreamDelta, None]:
        """Stream chat completion token and tool call deltas."""
        try:
            with mlflow.start_span(name="openrouter_stream_chat_with_tools") as span:
                span.set_inputs(
                    {
                        "model": model,
                        "message_count": len(messages),
                        "tool_count": len(tools),
                    }
                )
                delta_count = 0
                content_length = 0
                tool_call_delta_count = 0
                async with OpenRouter(
                    api_key=self.api_key,
                    http_referer=self.http_referer,
                    x_title=self.x_title,
                    timeout_ms=self.timeout_ms,
                ) as client:
                    stream = await client.chat.send_async(
                        model=model,
                        messages=cast(Any, messages),
                        tools=cast(Any, tools),
                        stream=True,
                        # Request reasoning tokens. OpenRouter ignores this for models
                        # that do not support it, so it degrades gracefully.
                        reasoning=cast(Any, {"effort": "low"}),
                    )
                    async with stream:
                        async for chunk in stream:
                            for delta in _extract_stream_deltas(chunk):
                                delta_count += 1
                                if delta.content:
                                    content_length += len(delta.content)
                                if delta.kind == "tool_call":
                                    tool_call_delta_count += 1
                                yield delta

                span.set_outputs(
                    {
                        "delta_count": delta_count,
                        "content_length": content_length,
                        "tool_call_delta_count": tool_call_delta_count,
                    }
                )
        except Exception as exc:  # noqa: BLE001
            raise InfraError(
                f"OpenRouter tool streaming request failed: {exc}"
            ) from exc

    async def generate_embeddings(
        self,
        *,
        model: str,
        texts: list[str],
        dimensions: int | None,
    ) -> list[list[float]]:
        """Generate embeddings for a batch of text inputs."""
        if not texts:
            return []

        try:
            with mlflow.start_span(name="openrouter_generate_embeddings") as span:
                span.set_inputs(
                    {
                        "model": model,
                        "text_count": len(texts),
                        "dimensions": dimensions,
                    }
                )
                async with OpenRouter(
                    api_key=self.api_key,
                    http_referer=self.http_referer,
                    x_title=self.x_title,
                    timeout_ms=self.timeout_ms,
                ) as client:
                    response = await client.embeddings.generate_async(
                        input=texts,
                        model=model,
                        dimensions=dimensions,
                    )

                response_any = cast(Any, response)
                sorted_data = sorted(response_any.data, key=lambda item: item.index)
                embeddings = [item.embedding for item in sorted_data]
                span.set_outputs(
                    {
                        "embedding_count": len(embeddings),
                        "embedding_dimensions": len(embeddings[0])
                        if embeddings
                        else 0,
                    }
                )
                return embeddings
        except Exception as exc:  # noqa: BLE001
            raise InfraError(f"OpenRouter embeddings request failed: {exc}") from exc

    async def send_chat_with_tools(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Send chat request with tool definitions and parse tool calls."""
        try:
            with mlflow.start_span(name="openrouter_send_chat_with_tools") as span:
                span.set_inputs(
                    {
                        "model": model,
                        "message_count": len(messages),
                        "tool_count": len(tools),
                    }
                )
                async with OpenRouter(
                    api_key=self.api_key,
                    http_referer=self.http_referer,
                    x_title=self.x_title,
                    timeout_ms=self.timeout_ms,
                ) as client:
                    response = await client.chat.send_async(
                        model=model,
                        messages=cast(Any, messages),
                        tools=cast(Any, tools),
                    )

                content = _extract_message_content(response)
                tool_calls = _extract_tool_calls(response)
                span.set_outputs(
                    {
                        "content_length": len(content),
                        "tool_call_count": len(tool_calls),
                    }
                )
                return {
                    "content": content,
                    "tool_calls": tool_calls,
                }
        except Exception as exc:  # noqa: BLE001
            raise InfraError(f"OpenRouter tool chat request failed: {exc}") from exc


def _extract_message_content(response: Any) -> str:
    choices = getattr(response, "choices", [])
    if not choices:
        return ""

    message = getattr(choices[0], "message", None)
    if message is None:
        return ""

    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ]
        return "".join(parts)

    return str(content)


def _extract_delta_content(chunk: Any) -> str:
    choices = getattr(chunk, "choices", [])
    if not choices:
        return ""

    delta = getattr(choices[0], "delta", None)
    if delta is None:
        return ""

    content = getattr(delta, "content", "")
    return content if isinstance(content, str) else ""


def _extract_stream_deltas(chunk: Any) -> list[ChatStreamDelta]:
    choices = getattr(chunk, "choices", [])
    if not choices:
        return []

    output: list[ChatStreamDelta] = []
    for choice in choices:
        delta = getattr(choice, "delta", None)
        if delta is None:
            continue

        content = getattr(delta, "content", "")
        if isinstance(content, str) and content:
            output.append(ChatStreamDelta(kind="content", content=content))

        reasoning = getattr(delta, "reasoning", "")
        if isinstance(reasoning, str) and reasoning:
            output.append(ChatStreamDelta(kind="reasoning", reasoning=reasoning))

        raw_tool_calls = getattr(delta, "tool_calls", None) or []
        for raw_call in raw_tool_calls:
            raw_index = getattr(raw_call, "index", None)
            index = int(raw_index) if isinstance(raw_index, (int, float)) else None
            function = getattr(raw_call, "function", None)
            tool_name = getattr(function, "name", None) if function else None
            arguments_delta = (
                getattr(function, "arguments", "") if function else ""
            )
            output.append(
                ChatStreamDelta(
                    kind="tool_call",
                    index=index,
                    call_id=getattr(raw_call, "id", None),
                    tool_name=tool_name if isinstance(tool_name, str) else None,
                    arguments_delta=arguments_delta
                    if isinstance(arguments_delta, str)
                    else "",
                )
            )

    return output


def _extract_tool_calls(response: Any) -> list[dict[str, Any]]:
    choices = getattr(response, "choices", [])
    if not choices:
        return []

    message = getattr(choices[0], "message", None)
    if message is None:
        return []

    raw_calls = getattr(message, "tool_calls", None)
    if not raw_calls:
        return []

    parsed_calls: list[dict[str, Any]] = []
    for call in raw_calls:
        call_id = getattr(call, "id", "")
        function = getattr(call, "function", None)
        if function is None:
            continue

        tool_name = getattr(function, "name", "")
        raw_arguments = getattr(function, "arguments", "{}")
        arguments: dict[str, Any]
        try:
            arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else {}
        except json.JSONDecodeError:
            arguments = {}

        parsed_calls.append(
            {
                "id": call_id,
                "name": tool_name,
                "arguments": arguments,
            }
        )

    return parsed_calls
