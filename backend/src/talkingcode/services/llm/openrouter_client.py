"""OpenRouter SDK adapter."""

from dataclasses import dataclass
from typing import Any, AsyncGenerator, Protocol

from openrouter import OpenRouter
import structlog

from talkingcode.errors import InfraError

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


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

    def stream_chat(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion delta content chunks."""

    async def generate_embeddings(
        self,
        *,
        model: str,
        texts: list[str],
        dimensions: int | None,
    ) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""


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
            async with OpenRouter(
                api_key=self.api_key,
                http_referer=self.http_referer,
                x_title=self.x_title,
                timeout_ms=self.timeout_ms,
            ) as client:
                response = await client.chat.send_async(
                    model=model,
                    messages=messages,
                    response_format=response_format,
                )

            return _extract_message_content(response)
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
            async with OpenRouter(
                api_key=self.api_key,
                http_referer=self.http_referer,
                x_title=self.x_title,
                timeout_ms=self.timeout_ms,
            ) as client:
                stream = await client.chat.send_async(
                    model=model,
                    messages=messages,
                    stream=True,
                )
                async with stream:
                    async for chunk in stream:
                        token = _extract_delta_content(chunk)
                        if token:
                            yield token
        except Exception as exc:  # noqa: BLE001
            raise InfraError(f"OpenRouter streaming request failed: {exc}") from exc

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

            sorted_data = sorted(response.data, key=lambda item: item.index)
            return [item.embedding for item in sorted_data]
        except Exception as exc:  # noqa: BLE001
            raise InfraError(f"OpenRouter embeddings request failed: {exc}") from exc


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
