import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

from opentelemetry.trace import get_tracer
from structlog import getLogger, stdlib

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.processing import run_transformation_pipeline
from talkingcode.shared.telemetry import async_log_failure, log_async_execution_time

from .pipeline_run_persistence import persistence_from_config

_run_lock = asyncio.Lock()
logger: stdlib.BoundLogger = getLogger("talkingcode")

tracer = get_tracer(__name__)


@dataclass(frozen=True, slots=True)
class PipelineRun:
    skipped: bool = False
    success: bool = False


def pipeline_currently_running() -> bool:
    """
    Check if the pipeline is currently running.
    This is used to prevent multiple instances of the pipeline from running at the same time.
    """
    return _run_lock.locked()


@log_async_execution_time
@tracer.start_as_current_span("download_and_persist_data")
@async_log_failure
async def download_and_persist_data(
    config: IngestionConfig,
    schedule_id: int | None = None,
) -> PipelineRun:
    """
    Download and persist data from the GitHub API to the database.
    This function is used to fetch data from the GitHub API and store it in the database.
    After fetching the data, the files are embedded and stored in the vector store.
    """
    if _run_lock.locked():
        logger.info("Pipeline is already running, skipping this execution")
        return PipelineRun(skipped=True)

    async with _run_lock:
        start_time = datetime.now()
        persistence = persistence_from_config(config)
        try:
            await run_transformation_pipeline(config)
            await persistence.create_pipeline_run(
                start_time=start_time,
                end_time=datetime.now(),
                success=True,
                error_message=None,
                associated_schedule=schedule_id,
            )
            return PipelineRun(success=True)
        except Exception as e:
            logger.exception(f"An error occurred while running the pipeline: {e}")
            await persistence.create_pipeline_run(
                start_time=start_time,
                end_time=datetime.now(),
                success=False,
                error_message=str(e),
            )
            return PipelineRun(success=False)


async def run_pipeline_on_schedule(
    config: IngestionConfig,
    hour: int,
    minute: int,
) -> None:
    """
    Run the pipeline on a given schedule every day at the specified hour and minute.

    Args:
        hour (int): The hour of the day to run the pipeline (24-hour format).
        minute (int): The minute of the hour to run the pipeline.
    """
    logger.info("Doing initial run of scheduled pipeline...")
    persistence = persistence_from_config(config)

    schedule = await persistence.create_schedule(hour, minute)
    pipeline_id = schedule.id

    await download_and_persist_data(config)
    logger.info("Initial run of scheduled pipeline completed.")
    schedule_active = True
    while schedule_active:
        await _sleep_until(hour, minute)
        persistence = persistence_from_config(config)
        schedule = await persistence.get_schedule(pipeline_id)
        if not schedule or not schedule.is_active:
            break
        logger.info("Running scheduled pipeline...")
        await download_and_persist_data(config, pipeline_id)
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
