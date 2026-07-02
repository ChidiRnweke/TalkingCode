"""Application startup helpers."""

from typing import Any

import mlflow
import structlog
from agents.tracing.span_data import TurnSpanData
from mlflow.openai import _agent_tracer
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

    _patch_openai_agents_turn_span_names()
    mlflow.openai.autolog()  # type: ignore
    logger.info(
        "mlflow.openai_agents_tracing.enabled",
        tracking_uri=config.mlflow_tracking_uri,
        experiment_name=config.mlflow_experiment_name,
    )


def _patch_openai_agents_turn_span_names() -> None:
    """Name OpenAI Agents turn spans until MLflow handles TurnSpanData directly."""
    original_get_span_name = _agent_tracer._get_span_name

    if getattr(original_get_span_name, "_talkingcode_patched", False):
        return

    def get_span_name(span_data: Any) -> str:
        if isinstance(span_data, TurnSpanData):
            return f"Turn {span_data.turn}: {span_data.agent_name}"

        return original_get_span_name(span_data)

    get_span_name._talkingcode_patched = True  # type: ignore[attr-defined]
    _agent_tracer._get_span_name = get_span_name


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
