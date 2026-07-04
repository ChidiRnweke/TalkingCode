"""Application startup helpers."""

import structlog
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from sqlalchemy import text

from talkingcode.config import AppConfig
from talkingcode.repository.database import get_engine
from talkingcode.telemetry import configure_telemetry

logger = structlog.getLogger(__name__)

_openai_agents_instrumented = False


def setup_openai_agents_tracing() -> None:
    """Instrument the OpenAI Agents SDK against the global tracer provider.

    Spans are exported via the OTLP endpoint configured in
    ``setup_telemetry_if_enabled``; a downstream OTel collector routes them to
    Phoenix (and any other backends) so the application never talks to Phoenix
    directly for tracing.  Idempotent: subsequent calls are no-ops.
    """
    global _openai_agents_instrumented
    if _openai_agents_instrumented:
        return
    OpenAIAgentsInstrumentor().instrument()
    _openai_agents_instrumented = True
    logger.info("openai_agents_tracing.enabled")


def disable_openai_native_tracing() -> None:
    """Disable the OpenAI Agents SDK's native trace exporter.

    The SDK runs a parallel tracer (``agents.tracing``) that exports to
    ``api.openai.com/v1/traces`` using ``OPENAI_API_KEY`` as a bearer token.
    We use OpenRouter (no ``OPENAI_API_KEY``), so every batch flush emits
    ``"OPENAI_API_KEY is not set, skipping trace export"``.  OpenInference
    spans routed via OpenTelemetry to the OTel collector are a separate path
    and are unaffected by this call.  Re-enabling native tracing (e.g. after
    switching to OpenAI-direct) means removing this call and setting
    ``OPENAI_API_KEY``.
    """
    from agents.tracing import set_trace_processors

    set_trace_processors([])
    logger.info("openai_native_tracing.disabled")


async def setup_database(config: AppConfig) -> None:
    engine = get_engine(config.database_url)
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await engine.dispose()


def setup_telemetry_if_enabled(config: AppConfig) -> None:
    if config.otel_exporter_endpoint:
        configure_telemetry(
            endpoint=config.otel_exporter_endpoint,
            service_name=config.otel_service_name,
            environment=config.otel_environment,
            phoenix_project=config.phoenix_project_name,
        )
        logger.info(
            "telemetry.enabled",
            endpoint=config.otel_exporter_endpoint,
            service_name=config.otel_service_name,
            phoenix_project=config.phoenix_project_name,
        )
    else:
        logger.info("telemetry.disabled")