"""Application startup helpers."""

import structlog
from phoenix.otel import register
from sqlalchemy import text

from talkingcode.config import AppConfig
from talkingcode.repository.database import get_engine
from talkingcode.telemetry import configure_telemetry

logger = structlog.getLogger(__name__)


def _collector_http_endpoint(grpc_endpoint: str) -> str:
    """Derive the OTLP/HTTP traces URL from the OTLP/gRPC endpoint.

    The OTel port convention is gRPC on :4317 and HTTP on :4318; the
    ``register`` exporter with ``protocol="http/protobuf"`` needs the HTTP
    endpoint with an explicit ``/v1/traces`` path.
    """
    return grpc_endpoint.replace(":4317", ":4318").rstrip("/") + "/v1/traces"


def setup_phoenix_tracing(config: AppConfig) -> None:
    """Configure Phoenix tracing routed through the OTel collector.

    ``register`` builds a Phoenix-flavored ``TracerProvider`` carrying the
    ``phoenix.project`` resource attribute (so the collector can route spans
    to the right Phoenix project) and, with ``auto_instrument=True``, wires
    the OpenAI Agents instrumentor to it.  The instrumentor's exclusive
    processor replaces the SDK's default backend exporter, which silences
    the ``OPENAI_API_KEY is not set`` warning when using OpenRouter.  The
    exporter points at the OTel collector; the collector adds the Phoenix
    ``Authorization: Bearer ...`` header and filters to OpenInference spans
    before forwarding to Phoenix.  The provider is not set as the global one
    so infrastructure telemetry (FastAPI/SQLAlchemy/HTTPX) stays on the
    vanilla OTel provider configured by ``setup_telemetry_if_enabled``.
    """
    if not config.otel_exporter_endpoint:
        logger.warning("phoenix.tracing.disabled", reason="missing_otel_endpoint")
        return

    register(
        endpoint=_collector_http_endpoint(config.otel_exporter_endpoint),
        protocol="http/protobuf",
        project_name=config.phoenix_project_name,
        set_global_tracer_provider=False,
        auto_instrument=True,
        batch=True,
        verbose=False,
    )
    logger.info(
        "phoenix.tracing.enabled",
        endpoint=config.otel_exporter_endpoint,
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