import logging

import structlog
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
from opentelemetry.trace import set_tracer_provider


def configure_telemetry(
    endpoint: str,
    service_name: str,
    environment: str,
    phoenix_project: str = "",
) -> None:
    """Configure telemetry for the application, including metrics, logs, and spans.

    ``phoenix_project`` is attached to the shared resource as ``phoenix.project``
    so a downstream OTel collector can route spans to the correct Phoenix project.
    """
    attributes = {
        "service.name": service_name,
        "deployment.environment": environment,
    }
    if phoenix_project:
        attributes["phoenix.project"] = phoenix_project
    resource = Resource.create(attributes)

    _configure_metrics(endpoint, resource)
    _configure_logs(endpoint, resource)
    _configure_spans(endpoint, resource)


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

    handler = LoggingHandler(level=logging.DEBUG, logger_provider=logger_provider)
    _configure_structlog()

    logging.getLogger("talkingcode").addHandler(handler)
    logging.getLogger("talkingcode").setLevel(logging.DEBUG)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)


def _configure_structlog() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
