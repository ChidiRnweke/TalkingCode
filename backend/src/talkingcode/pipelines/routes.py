from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.background import BackgroundTasks

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.pipelines.orchestration import (
    download_and_persist_data,
    persistence_from_config,
    pipeline_currently_running,
    run_pipeline_on_schedule,
)


@dataclass(frozen=True, slots=True)
class PipelineStarted:
    message: str


@dataclass(frozen=True, slots=True)
class PipelineCurrentlyRunning:
    running: bool


@dataclass(frozen=True, slots=True)
class PipelineRunResponse:
    id: int
    start_time: datetime
    end_time: datetime
    associated_schedule: Optional[int]
    success: bool
    error_message: Optional[str]


@dataclass(frozen=True, slots=True)
class PipelineScheduleResponse:
    id: int
    hour: int
    minute: int
    is_active: bool


router = APIRouter(prefix="/ingest")


def get_ingestion_config(request: Request) -> IngestionConfig:
    config = cast(IngestionConfig, request.state.ingestion_config)
    return config


@router.get("/pipeline/run")
async def check_if_pipeline_running() -> PipelineCurrentlyRunning:
    """
    Check if the pipeline is currently running.
    This endpoint returns a boolean indicating whether the pipeline is currently running or not.


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


@router.get("/pipeline/history", response_model=List[PipelineRunResponse])
async def get_pipeline_run_history(
    config: IngestionConfig = Depends(get_ingestion_config),
) -> List[PipelineRunResponse]:
    """
    Get the history of all pipeline runs.

    Returns:
        List[PipelineRunResponse]: A list of all pipeline run records.
    """
    persistence = persistence_from_config(config)
    runs = await persistence.get_run_history()
    return [
        PipelineRunResponse(
            id=run.id,
            start_time=run.start_time,
            end_time=run.end_time,
            associated_schedule=run.associated_schedule,
            success=run.success,
            error_message=run.error_message,
        )
        for run in runs
    ]


@router.get("/pipeline/schedules")
async def get_pipeline_schedules(
    config: IngestionConfig = Depends(get_ingestion_config),
) -> List[PipelineScheduleResponse]:
    """
    Get all pipeline schedules.

    Returns:
        List[PipelineScheduleResponse]: A list of all pipeline schedule records.
    """
    persistence = persistence_from_config(config)
    schedules = await persistence.get_schedules()
    return [
        PipelineScheduleResponse(
            id=schedule.id,
            hour=schedule.hour,
            minute=schedule.minute,
            is_active=schedule.is_active,
        )
        for schedule in schedules
    ]


@router.get("/pipeline/schedule/{schedule_id}")
async def get_pipeline_runs_by_schedule(
    schedule_id: int,
    config: IngestionConfig = Depends(get_ingestion_config),
) -> List[PipelineRunResponse]:
    """
    Get all pipeline runs associated with a specific schedule.

    Args:
        schedule_id (int): The ID of the pipeline schedule.

    Returns:
        List[PipelineRunResponse]: A list of pipeline run records associated with the schedule.
    """
    persistence = persistence_from_config(config)
    runs = await persistence.get_runs_by_schedule(str(schedule_id))
    return [
        PipelineRunResponse(
            id=run.id,
            start_time=run.start_time,
            end_time=run.end_time,
            associated_schedule=run.associated_schedule,
            success=run.success,
            error_message=run.error_message,
        )
        for run in runs
    ]


@router.get("/pipeline/schedule/{schedule_id}")
async def get_pipeline_schedule(
    schedule_id: int,
    config: IngestionConfig = Depends(get_ingestion_config),
) -> PipelineScheduleResponse:
    """
    Get a pipeline schedule by its ID.

    Args:
        schedule_id (int): The ID of the pipeline schedule.

    Returns:
        PipelineScheduleResponse: The pipeline schedule record.
    """
    persistence = persistence_from_config(config)
    schedule = await persistence.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    return PipelineScheduleResponse(
        id=schedule.id,
        hour=schedule.hour,
        minute=schedule.minute,
        is_active=schedule.is_active,
    )
