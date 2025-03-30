from dataclasses import dataclass
from typing import cast

from fastapi import APIRouter, Depends, Request
from fastapi.background import BackgroundTasks

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.orchestration import (
    download_and_persist_data,
    pipeline_currently_running,
    run_pipeline_on_schedule,
)


@dataclass(frozen=True, slots=True)
class PipelineStarted:
    message: str


@dataclass(frozen=True, slots=True)
class PipelineCurrentlyRunning:
    running: bool


router = APIRouter()


def get_ingestion_config(request: Request) -> IngestionConfig:
    config = cast(IngestionConfig, request.state.ingestion_config)
    return config


@router.get("/pipeline/run")
async def check_if_pipeline_running() -> PipelineCurrentlyRunning:
    """
    Check if the pipeline is currently running.
    This endpoint returns a boolean indicating whether the pipeline is currently running or not.
    This is used to prevent multiple instances of the pipeline from running at the same time.
    This is useful for debugging and monitoring purposes.

    Returns
        PipelineCurrentlyRunning: A message indicating whether the pipeline is currently running or not.
    """
    running = pipeline_currently_running()
    return PipelineCurrentlyRunning(running=running)


@router.post("/pipeline/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    config: IngestionConfig = Depends(get_ingestion_config),
) -> PipelineStarted:
    """
    Start the pipeline run immediately. If a pipeline run is already in progress, it will be skipped.
    NOTE: This isn't done in a particularly elegant way. Uvicorn can be run with multiple workers,
    that means that multiple requests can be sent to this endpoint at the same time, these will
    not share the same lock. This means that multiple pipeline runs can be started at the same time.

    Returns:
        PipelineStarted: A message indicating the pipeline run status. Returns immediately
        after starting the pipeline run in the background.
    """
    background_tasks.add_task(download_and_persist_data, config)
    return PipelineStarted(message="Pipeline run started.")


@router.post("/pipeline/schedule")
async def schedule_pipeline(
    hour: int,
    minute: int,
    background_tasks: BackgroundTasks,
    config: IngestionConfig = Depends(get_ingestion_config),
) -> PipelineStarted:
    """
    Schedule the pipeline to run at a specific time every day.
    This endpoint accepts the hour and minute in 24-hour format.
    NOTE: This isn't done in a particularly elegant way. Uvicorn can be run with multiple workers,
    that means that multiple requests can be sent to this endpoint at the same time, these will
    not share the same lock. This means that multiple pipeline runs can be scheduled at the same time.
    This is a problem because the scheduled pipeline will run at the same time as the other
    scheduled pipeline.

    Args:
        hour (int): The hour of the day to run the pipeline (24-hour format).
        minute (int): The minute of the hour to run the pipeline.

    Returns:
        PipelineStarted: A message indicating the pipeline schedule status.
    """
    background_tasks.add_task(run_pipeline_on_schedule, config, hour, minute)
    return PipelineStarted(
        message=f"Pipeline scheduled to run at {hour:02d}:{minute:02d}."
    )
