from opentelemetry.sdk.resources import Resource

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.metrics import set_meter_provider
from opentelemetry._logs import set_logger_provider
from opentelemetry.trace import set_tracer_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import logging


def configure_telemetry(telemetry_endpoint: str):
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
