from contextlib import contextmanager
from typing import Any, Callable, ParamSpec, TypeVar


@contextmanager
def suppress_stack_trace():
    """Suppresses the decorator's code from appearing in stack traces."""
    try:
        yield
    except Exception:
        raise


T = TypeVar("T")
P = ParamSpec("P")
C = TypeVar("C", bound=type)


def function_metadata(func: Callable[P, T]) -> dict[str, Any]:
    module = {"module": func.__module__}
    _class = {"class": func.__qualname__.split(".")[0]}
    _function = {"function": func.__qualname__.split(".")[-1]}
    file_name = {"file_name": func.__code__.co_filename}
    line_number = {"line_number": func.__code__.co_firstlineno}
    return {**module, **_class, **_function, **file_name, **line_number}
