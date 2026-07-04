"""Session propagation for OpenInference traces."""

from collections.abc import AsyncGenerator, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from openinference.instrumentation.context_attributes import using_session

P = ParamSpec("P")
T = TypeVar("T")


def with_session(
    extract_session_id: Callable[..., str | None],
) -> Callable[
    [Callable[P, AsyncGenerator[T, None]]],
    Callable[P, AsyncGenerator[T, None]],
]:
    """Decorator that propagates a session ID via OTel context to child spans.

    ``extract_session_id`` receives the wrapped call's args/kwargs and returns
    a session ID string, or ``None`` to skip session propagation.  OpenInference
    instrumentors (e.g. the OpenAI Agents instrumentor) read the context set by
    ``using_session`` and stamp ``session.id`` on every span they create inside
    the wrapped block, so Phoenix groups those spans into a session.

    The extractor must accept the same positional args as the wrapped callable,
    including ``self`` for bound methods — e.g.
    ``lambda self, *, turn, **_kw: ...``.
    """

    def decorator(
        fn: Callable[P, AsyncGenerator[T, None]],
    ) -> Callable[P, AsyncGenerator[T, None]]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> AsyncGenerator[T, None]:
            session_id = extract_session_id(*args, **kwargs)
            if session_id is None:
                async for event in fn(*args, **kwargs):
                    yield event
                return
            with using_session(session_id):
                async for event in fn(*args, **kwargs):
                    yield event

        return wrapper

    return decorator