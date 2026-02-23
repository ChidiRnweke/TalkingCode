import logging
import structlog
from typing import Any

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_current_span, set_tracer_provider


def configure_telemetry(endpoint: str, service_name: str, environment: str) -> None:
    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": environment,
        }
    )

    _configure_spans(endpoint, resource)
    _configure_metrics(endpoint, resource)
    _configure_logs(endpoint, resource)


def _configure_spans(endpoint: str, resource: Resource) -> None:
    span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    set_tracer_provider(tracer_provider)


def _configure_metrics(endpoint: str, resource: Resource) -> None:
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider([metric_reader], resource)
    set_meter_provider(meter_provider)


def _configure_logs(endpoint: str, resource: Resource) -> None:
    log_exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)

    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger("talkingcode").addHandler(handler)
    logging.getLogger("talkingcode").setLevel(logging.INFO)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_span_context,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _add_span_context(_: Any, __: Any, event_dict: dict[str, Any]) -> dict[str, Any]:
    span = get_current_span()
    if not span.is_recording():
        return event_dict
    ctx = span.get_span_context()
    event_dict["trace_id"] = hex(ctx.trace_id)
    event_dict["span_id"] = hex(ctx.span_id)
    return event_dict
