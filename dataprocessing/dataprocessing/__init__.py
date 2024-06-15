import os
from dagster import (
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)
from dotenv import load_dotenv
from dataprocessing.orchestration.resources import AppConfigResource
from .orchestration import assets
from shared.log import setup_custom_logger
from alembic.config import Config
from alembic import command

logger = setup_custom_logger("app_logger")
if not os.getenv("PRODUCTION"):
    logger.warning("Running in development mode")
    load_dotenv("../config/.env.secret.dev")


def run_migrations() -> None:
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "../shared/shared/migrations")
    command.upgrade(alembic_cfg, "head")
    logger.info("Migrations run successfully")


run_migrations()

all_assets = load_assets_from_modules([assets])
all_assets_job = define_asset_job(name="all_assets_job")

ingestion_schedule = ScheduleDefinition(
    job=all_assets_job,
    cron_schedule="0 0 * * *",
)

defs = Definitions(
    assets=all_assets,
    resources={"app_config_resource": AppConfigResource.from_env()},
    schedules=[ingestion_schedule],
)
