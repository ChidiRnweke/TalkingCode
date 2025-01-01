import logging

import structlog
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
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
    _configure_structlog()

    structlog.getLogger("talkingcode").addHandler(handler)
    structlog.getLogger("talkingcode").setLevel(logging.DEBUG)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)


def _configure_structlog():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_open_telemetry_spans,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _add_open_telemetry_spans(_, __, event_dict):
    span = get_current_span()
    if not span.is_recording():
        event_dict["span"] = None
        return event_dict

    ctx = span.get_span_context()
    parent = getattr(span, "parent", None)

    event_dict["span"] = {
        "span_id": hex(ctx.span_id),
        "trace_id": hex(ctx.trace_id),
        "parent_span_id": None if not parent else hex(parent.span_id),
    }

    return event_dict
