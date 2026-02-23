import asyncio
import os
import subprocess
import sys

import structlog
from talkingcode.scripts.provision_db import provision_database
from talkingcode.telemetry import configure_telemetry
from talkingcode.config import AppConfig

logger = structlog.getLogger("talkingcode.migrate")


async def run() -> None:
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
        await provision_database()
        
        # 3. Run Alembic upgrade head
        logger.info("migrate.alembic.starting")
        # Use sys.executable to ensure we use the same python/venv
        # but the plan says "uv run alembic upgrade head"
        # We can use subprocess.run
        proc = subprocess.run(["alembic", "upgrade", "head"], check=False)
        if proc.returncode != 0:
            logger.error("migrate.alembic.failed", exit_code=proc.returncode)
            sys.exit(proc.returncode)
            
        logger.info("migrate.completed")
    except Exception as exc:
        logger.error("migrate.failed", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run())
