import asyncio
from datetime import datetime, timedelta
from logging import getLogger

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.processing import run_transformation_pipeline
from talkingcode.shared.telemetry import log_execution_time

_run_lock = asyncio.Lock()
logger = getLogger(__name__)


@log_execution_time
async def download_and_persist_data() -> None:
    """
    Download and persist data from the GitHub API to the database.
    This function is used to fetch data from the GitHub API and store it in the database.
    After fetching the data, the files are embedded and stored in the vector store.
    """
    async with _run_lock:
        app_config = IngestionConfig.from_env()
        try:
            await run_transformation_pipeline(app_config)
        except Exception as e:
            logger.exception(f"An error occurred while running the pipeline: {e}")


async def run_pipeline_on_schedule(hour: int, minute: int) -> None:
    """
    Run the pipeline on a given schedule every day at the specified hour and minute.

    Args:
        hour (int): The hour of the day to run the pipeline (24-hour format).
        minute (int): The minute of the hour to run the pipeline.
    """
    logger.info("Doing initial run of scheduled pipeline...")
    await download_and_persist_data()
    while True:
        await _sleep_until(hour, minute)

        logger.info("Running scheduled pipeline...")
        await download_and_persist_data()
        logger.info("Scheduled pipeline completed.")


async def _sleep_until(hour: int, minute: int) -> None:
    """
    Asynchronously sleep until the next occurrence of the specified hour and minute.

    Args:
        hour (int): The hour of the day to sleep until (24-hour format).
        minute (int): The minute of the hour to sleep until.
    """
    now = datetime.now()
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if next_run < now:
        next_run += timedelta(days=1)

    sleep_duration = (next_run - now).total_seconds()
    logger.info(f"Sleeping until the next run at {next_run}...")
    await asyncio.sleep(sleep_duration)
