"""Application startup helpers."""

import mlflow
import structlog
from sqlalchemy import text

from talkingcode.config import AppConfig
from talkingcode.repository.database import get_engine
from talkingcode.telemetry import configure_telemetry

logger = structlog.getLogger(__name__)


def configure_mlflow_tracing(config: AppConfig) -> None:
    if not config.mlflow_tracking_uri:
        logger.warning("mlflow.tracing.disabled", reason="missing_tracking_uri")
        return

    mlflow.set_tracking_uri(config.mlflow_tracking_uri)

    if config.mlflow_experiment_name:
        mlflow.set_experiment(experiment_name=config.mlflow_experiment_name)

    mlflow.openai.autolog()
    logger.info(
        "mlflow.openai_agents_tracing.enabled",
        tracking_uri=config.mlflow_tracking_uri,
        experiment_name=config.mlflow_experiment_name,
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
