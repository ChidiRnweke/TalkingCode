"""Unit tests for the ``with_session`` decorator."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from opentelemetry.context import get_value
from openinference.semconv.trace import SpanAttributes

from talkingcode.telemetry import with_session


async def _stream_events(
    events: list[Any], captured: list[Any]
) -> AsyncGenerator[Any, None]:
    # Capture the context value seen by code running inside the wrapped
    # generator.  OpenInference instrumentors read this same context value
    # and stamp it as the ``session.id`` span attribute.
    captured.append(get_value(SpanAttributes.SESSION_ID))
    for event in events:
        yield event


@with_session(lambda *, events, session_id, captured, **_kw: session_id)
async def decorated_generator(
    *, events: list[Any], session_id: str | None, captured: list[Any]
) -> AsyncGenerator[Any, None]:
    async for event in _stream_events(events, captured):
        yield event


@pytest.mark.asyncio
async def test_with_session_propagates_session_id_into_context() -> None:
    captured: list[Any] = []

    async for _event in decorated_generator(
        events=["a", "b"], session_id="conv-123", captured=captured
    ):
        pass

    assert captured == ["conv-123"]


@pytest.mark.asyncio
async def test_with_session_skips_propagation_when_extractor_returns_none() -> None:
    captured: list[Any] = []

    async for _event in decorated_generator(
        events=["a"], session_id=None, captured=captured
    ):
        pass

    assert captured == [None]


@pytest.mark.asyncio
async def test_with_session_yields_all_events() -> None:
    yielded: list[Any] = []

    async for event in decorated_generator(
        events=["a", "b", "c"], session_id="conv-123", captured=[]
    ):
        yielded.append(event)

    assert yielded == ["a", "b", "c"]


class _Service:
    @with_session(lambda self, *, session_id, captured, **_kw: session_id)
    async def stream(
        self, *, session_id: str | None, captured: list[Any]
    ) -> AsyncGenerator[Any, None]:
        captured.append(get_value(SpanAttributes.SESSION_ID))
        yield "x"


@pytest.mark.asyncio
async def test_with_session_propagates_session_id_on_bound_method() -> None:
    captured: list[Any] = []

    async for _event in _Service().stream(session_id="conv-bound", captured=captured):
        pass

    assert captured == ["conv-bound"]