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