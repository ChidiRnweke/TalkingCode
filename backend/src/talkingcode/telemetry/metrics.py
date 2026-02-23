import asyncio
import inspect
import time
from functools import wraps
from typing import Any, Callable, Coroutine

from opentelemetry.metrics import get_meter
from structlog import getLogger

from .helpers import C, P, T, function_metadata, suppress_stack_trace


def instrument_all_async(
    decorator: Callable[
        [Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]]
    ],
) -> Callable[[C], C]:
    """A class decorator that applies `decorator` to every public async method in the class."""

    def class_decorator(cls: C) -> C:
        for attr_name, attr_value in list(cls.__dict__.items()):
            if attr_name.startswith("_"):
                continue
            if not inspect.iscoroutinefunction(attr_value):
                continue
            setattr(cls, attr_name, decorator(attr_value))
        return cls

    return class_decorator


def instrument_all_sync(
    decorator: Callable[[Callable[P, T]], Callable[P, T]],
) -> Callable[[C], C]:
    """A class decorator that applies `decorator` to every public non-async method in the class."""

    def class_decorator(cls: C) -> C:
        for attr_name, attr_value in list(cls.__dict__.items()):
            if attr_name.startswith("_"):
                continue
            if not inspect.isfunction(attr_value) or inspect.iscoroutinefunction(
                attr_value
            ):
                continue
            setattr(cls, attr_name, decorator(attr_value))
        return cls

    return class_decorator


def log_execution_time(func: Callable[P, T]) -> Callable[P, T]:
    """Decorator to log execution time for functions via histogram metric."""
    meter = get_meter(__name__)
    execution_time_histogram = meter.create_histogram(
        name=f"{func.__name__}_execution_time",
        description="Execution time of functions",
        unit="seconds",
    )
    attributes = function_metadata(func)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        with suppress_stack_trace():
            try:
                result = func(*args, **kwargs)
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                execution_time_histogram.record(execution_time, attributes=attributes)
            return result

    return wrapper


def log_async_execution_time(
    func: Callable[P, Coroutine[Any, Any, T]],
) -> Callable[P, Coroutine[Any, Any, T]]:
    """Decorator to log execution time for asynchronous functions via histogram metric."""
    meter = get_meter(__name__)
    execution_time_histogram = meter.create_histogram(
        name=f"{func.__name__}_execution_time",
        description="Execution time of functions",
        unit="seconds",
    )

    attributes = function_metadata(func)
    func = _measure_blocking_time(func)

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
        with suppress_stack_trace():
            try:
                result = await func(*args, **kwargs)
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                execution_time_histogram.record(execution_time, attributes=attributes)
            return result

    return wrapper


def _measure_blocking_time(
    f: Callable[P, Coroutine[Any, Any, T]],
) -> Callable[P, Coroutine[Any, Any, T]]:
    meter = get_meter(__name__)
    blocking_time_histogram = meter.create_histogram(
        name=f"{f.__name__}_blocking_time",
        description="Measures the time a function blocks the event loop",
        unit="seconds",
    )
    blocking_counter = meter.create_counter(
        name=f"{f.__name__}_blocking_count",
        description="Number of times the function blocked the event loop for over 100ms",
        unit="count",
    )
    attributes = function_metadata(f)

    @wraps(f)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        loop = asyncio.get_running_loop()
        start_time = time.perf_counter()

        with suppress_stack_trace():
            task = loop.create_task(f(*args, **kwargs))
            while not task.done():
                loop_start = time.perf_counter()
                await asyncio.sleep(0)
                loop_end = time.perf_counter()

                blocking_time = loop_end - loop_start
                if blocking_time > 0.1:
                    blocking_counter.add(1)
                    blocking_time_histogram.record(blocking_time, attributes=attributes)

            result = await task
            total_time = time.perf_counter() - start_time
            blocking_time_histogram.record(total_time, attributes=attributes)
            return result

    return wrapper
