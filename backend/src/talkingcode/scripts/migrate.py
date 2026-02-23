"""Run database provisioning then Alembic migrations.

Uses Alembic's Python API instead of shelling out to the CLI.
"""

import asyncio
import os
import sys
from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config

from talkingcode.config import AppConfig
from talkingcode.scripts.provision_db import provision_database
from talkingcode.telemetry import configure_telemetry

logger = structlog.getLogger("talkingcode.migrate")

# backend/ is 3 parents up from backend/src/talkingcode/scripts/
_BACKEND_DIR = Path(__file__).resolve().parents[3]


def _get_alembic_config() -> Config:
    ini_path = _BACKEND_DIR / "alembic.ini"
    if not ini_path.exists():
        raise FileNotFoundError(f"alembic.ini not found at {ini_path}")
    return Config(str(ini_path))


def run() -> None:
    # 1. Initialize telemetry
    config = AppConfig.from_env()
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    service_name = os.getenv("OTEL_SERVICE_NAME", "talkingcode-migrate")
    otel_env = os.getenv("OTEL_ENVIRONMENT", config.environment)

    if endpoint:
        configure_telemetry(endpoint=endpoint, service_name=service_name, environment=otel_env)
        logger.info("telemetry.enabled")

    try:
        # 2. Run provision function
        logger.info("migrate.provision.starting")
        asyncio.run(provision_database())
        logger.info("migrate.provision.completed")

        # 3. Run Alembic upgrade head via Python API
        logger.info("migrate.alembic.starting")
        alembic_cfg = _get_alembic_config()
        command.upgrade(alembic_cfg, "head")
        logger.info("migrate.completed")

    except SystemExit:
        raise
    except Exception as exc:
        logger.error("migrate.failed", error=str(exc), error_type=type(exc).__name__)
        sys.exit(1)


if __name__ == "__main__":
    run()
