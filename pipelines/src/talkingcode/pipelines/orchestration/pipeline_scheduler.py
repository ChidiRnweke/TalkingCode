import asyncio
from datetime import datetime, timedelta
from logging import getLogger

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.processing import (
    EmbeddingService,
    IngestionService,
)

_persist_data_lock = asyncio.Lock()
_persist_embeddings_lock = asyncio.Lock()
logger = getLogger(__name__)


async def persist_data() -> None:
    """
    Persist data from the GitHub API to the database.

    Args:
        app_config_resource (AppConfigResource): The application configuration.
        It is a resource class because the dagster framework requires
        it to be so.
    """
    async with _persist_data_lock:
        app_config = IngestionConfig.from_env()
        ingestion_service = IngestionService.from_config(app_config)
        await ingestion_service.fetch_and_persist_data()


async def persist_embeddings() -> None:
    """
    Persist embeddings of the files in the database.
    This function depends on the `persist_data` asset to run first.

    Args:
        app_config_resource (AppConfigResource): The application configuration.
        It is a resource class because the dagster framework requires it to be so.
    """
    async with _persist_embeddings_lock:
        app_config = IngestionConfig.from_env()
        embedding_service = EmbeddingService.from_config(app_config)
        await embedding_service.embed_and_persist_files()


async def run_pipeline_on_schedule(hour: int, minute: int) -> None:
    """
    Run the pipeline on a given schedule every day at the specified hour and minute.

    Args:
        hour (int): The hour of the day to run the pipeline (24-hour format).
        minute (int): The minute of the hour to run the pipeline.
    """
    while True:
        await _sleep_until(hour, minute)

        logger.info("Running scheduled pipeline...")
        await persist_data()
        await persist_embeddings()


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
    await asyncio.sleep(sleep_duration)
