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

if not os.getenv("PRODUCTION"):
    load_dotenv("../config/.env.secret.dev")

logger = setup_custom_logger("app_logger")


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
