from functools import wraps
from typing import Any, Callable, Coroutine

import structlog

from .helpers import P, T, function_metadata, suppress_stack_trace


def async_log_failure(
    func: Callable[P, Coroutine[Any, Any, T]],
) -> Callable[P, Coroutine[Any, Any, T]]:
    """
    Decorator to log exceptions raised by asynchronous functions.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """

    attributes = function_metadata(func)

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        with suppress_stack_trace():
            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                logger = structlog.getLogger("talkingcode")
                logger.exception(e, stack_info=True, stacklevel=5, extra=attributes)
                raise e
            return result

    return wrapper


def log_failure(func: Callable[P, T]) -> Callable[P, T]:
    """
    Decorator to log exceptions raised by functions.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function.
    """

    attributes = function_metadata(func)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger = structlog.getLogger("talkingcode")
            logger.exception(e, stack_info=True, stacklevel=5, extra=attributes)
            raise e
        return result

    return wrapper
