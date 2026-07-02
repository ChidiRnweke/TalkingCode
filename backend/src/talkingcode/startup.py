"""Application startup helpers."""

import structlog
from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from phoenix.otel import register
from sqlalchemy import text

from talkingcode.config import AppConfig
from talkingcode.repository.database import get_engine
from talkingcode.telemetry import configure_telemetry

logger = structlog.getLogger(__name__)

_phoenix_configured = False


def configure_phoenix_tracing(config: AppConfig) -> None:
    global _phoenix_configured
    if not config.phoenix_collector_endpoint:
        logger.warning("phoenix.tracing.disabled", reason="missing_collector_endpoint")
        return

    if _phoenix_configured:
        return

    if not config.phoenix_api_key:
        logger.error(
            "phoenix.tracing.misconfigured",
            reason="missing_api_key",
            endpoint=config.phoenix_collector_endpoint,
        )

    # Phoenix must not own the global tracer provider: app telemetry
    # (FastAPI/SQLAlchemy/HTTPX -> otel-collector) keeps it; only the
    # OpenAI Agents instrumentor exports to Phoenix.
    tracer_provider = register(
        endpoint=f"{config.phoenix_collector_endpoint.rstrip('/')}/v1/traces",
        protocol="http/protobuf",
        project_name=config.phoenix_project_name,
        api_key=config.phoenix_api_key or None,
        set_global_tracer_provider=False,
        batch=True,
        verbose=False,
    )
    OpenAIAgentsInstrumentor().instrument(tracer_provider=tracer_provider)
    _phoenix_configured = True
    logger.info(
        "phoenix.openai_agents_tracing.enabled",
        endpoint=config.phoenix_collector_endpoint,
        project_name=config.phoenix_project_name,
    )


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
        )
        logger.info(
            "telemetry.enabled",
            endpoint=config.otel_exporter_endpoint,
            service_name=config.otel_service_name,
        )
    else:
        logger.info("telemetry.disabled")
