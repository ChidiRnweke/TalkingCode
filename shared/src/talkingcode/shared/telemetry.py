import asyncio
import inspect
import logging
import time
from functools import wraps
from logging import getLogger
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import get_meter, set_meter_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer, set_tracer_provider

T = TypeVar("T")
P = ParamSpec("P")
C = TypeVar("C", bound=type)


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


def run_in_span(name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    tracer = get_tracer(__name__)

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            with tracer.start_as_current_span(name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def async_run_in_span(
    name: str,
) -> Callable[
    [Callable[P, Coroutine[Any, Any, T]]], Callable[P, Coroutine[Any, Any, T]]
]:
    tracer = get_tracer(__name__)

    def decorator(
        func: Callable[P, Coroutine[Any, Any, T]],
    ) -> Callable[P, Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Create a new span for each invocation of the function
            with tracer.start_as_current_span(name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


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
    attributes = _function_metadata(func)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
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

    attributes = _function_metadata(func)
    func = _measure_blocking_time(func)

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = time.time()
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
    attributes = _function_metadata(f)

    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        coroutine = f(*args, **kwargs)
        fut = asyncio.Future()
        s = time.perf_counter()

        def done(arg=None):
            try:
                next_ = coroutine.send(arg)
                next_.add_done_callback(done)
            except StopIteration as e:
                block_time = round(time.perf_counter() - s, 2)
                blocking_time_histogram.record(block_time, attributes=attributes)
                if block_time > 0.1:
                    blocking_counter.add(1)
                fut.set_result(e.value)

        done()
        return await fut

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

    attributes = _function_metadata(func)

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            result = await func(*args, **kwargs)
        except Exception as e:
            logger = getLogger("app_logger")
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

    attributes = _function_metadata(func)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger = getLogger("app_logger")
            logger.exception(e, stack_info=True, stacklevel=5, extra=attributes)
            raise e
        return result

    return wrapper


def configure_telemetry(telemetry_endpoint: str) -> None:
    """
    Configure telemetry for the application, including metrics, logs, and spans to
    your telemetry endpoint.

    Args:
        telemetry_endpoint (str): The endpoint to send telemetry data to.
    """
    resource = Resource.create({"service.name": "TalkingCode"})
    _configure_metrics(telemetry_endpoint, resource)
    _configure_logs(telemetry_endpoint, resource)
    _configure_spans(telemetry_endpoint, resource)


def _configure_spans(endpoint: str, telemetry_resource: Resource):
    span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    tracer_provider = TracerProvider(resource=telemetry_resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    set_tracer_provider(tracer_provider)


def _configure_metrics(endpoint: str, telemetry_resource: Resource):
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider([metric_reader], telemetry_resource)
    set_meter_provider(meter_provider)


def _configure_logs(endpoint: str, telemetry_resource: Resource):
    log_exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)

    logger_provider = LoggerProvider(resource=telemetry_resource)

    handler = LoggingHandler(level=logging.DEBUG, logger_provider=logger_provider)
    logging.getLogger("app_logger").addHandler(handler)
    logging.getLogger("app_logger").setLevel(logging.DEBUG)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)


def _function_metadata(func: Callable[P, T]) -> dict[str, Any]:
    module = {"module": func.__module__}
    _class = {"class": func.__qualname__.split(".")[0]}
    _function = {"function": func.__qualname__.split(".")[-1]}
    file_name = {"file_name": func.__code__.co_filename}
    line_number = {"line_number": func.__code__.co_firstlineno}
    return {**module, **_class, **_function, **file_name, **line_number}
