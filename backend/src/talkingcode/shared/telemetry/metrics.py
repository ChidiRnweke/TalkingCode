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
    """
    A class decorator that applies `decorator` to every public async method in the class.
    Each method is decorated with the provided `decorator`.

    Example:

    ```python
    import asyncio

    @instrument_all_async(log_async_execution_time)
    class MyClass:
        async def sleep_for(self, seconds: int) -> None:
            await asyncio.sleep(seconds)

    my_class = MyClass()
    await my_class.sleep_for(1) # This will log the execution time of the method

    ```

    Args:
        decorator (Callable[ [Callable[..., Coroutine[Any, Any, T]]], Callable[..., Coroutine[Any, Any, T]] ]): The decorator to apply to each async method.

    Returns:
        Callable[C, C]: The instrumented class.
    """

    def class_decorator(cls: C) -> C:
        for attr_name, attr_value in list(cls.__dict__.items()):
            # Only decorate non-underscore async methods
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
    """
    A class decorator that applies `decorator` to every public non-async method in the class.
    Each method is decorated with the provided `decorator`. This decorator will not decorate
    methods that are already decorated with `@instrument_all_async`.

    Args:
        decorator (Callable[[Callable[P, T]], Callable[P, T]]): The decorator to apply to each sync method.

    Returns:
        Callable[C, C]: The instrumented class.
    """

    def class_decorator(cls: C) -> C:
        for attr_name, attr_value in list(cls.__dict__.items()):
            # Only decorate non-underscore sync methods
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
    """
    Decorator to log execution time for functions. This decorator will create a
    histogram metric for the function that records the execution time of the function.

    If open telemetry is not configured, this decorator will use a no-op meter.

    Args:
        func (Callable[P, T]): The function to decorate.

    Returns:
        Callable[P, T]: The decorated function.
    """
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
    """
    Decorator to log execution time for asynchronous functions. This decorator will
    create a histogram metric for the function that records the execution time of the
    function.

    If open telemetry is not configured, this decorator will use a no-op meter.

    Args:
        func (Callable[P, Coroutine[Any, Any, T]]): The function to decorate.

    Returns:
        Callable[P, Coroutine[Any, Any, T]]: The decorated function.
    """
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
                logger = getLogger("talkingcode")
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
            logger = getLogger("talkingcode")
            logger.exception(e, stack_info=True, stacklevel=5, extra=attributes)
            raise e
        return result

    return wrapper
