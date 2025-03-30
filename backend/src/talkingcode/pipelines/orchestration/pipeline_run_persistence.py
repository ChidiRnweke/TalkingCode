from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from talkingcode.pipelines.config import IngestionConfig
from talkingcode.shared.database import PipelineRunModel, PipelineScheduleModel
from talkingcode.shared.telemetry import instrument_all_async, log_async_execution_time

logger: structlog.stdlib.BoundLogger = structlog.getLogger("talkingcode")


class PipelineStorage(Protocol):
    async def create_pipeline_run(
        self, associated_schedule: str | None = None
    ) -> PipelineRunModel:
        """
        Create a new pipeline run record in the database.
        This method initializes a new pipeline run with the current timestamp and an optional associated schedule.
        The pipeline run is added to the session and committed to the database.
        The ID of the created pipeline run is logged for tracking purposes.

        Args:
            associated_schedule (Optional[str], optional): An optional schedule associated with the pipeline run. Defaults to None.

        Returns:
            PipelineRunModel: The created pipeline run record.
        """
        ...

    async def get_schedule(self, schedule_id: str) -> PipelineScheduleModel | None:
        """
        Get a pipeline schedule by its ID.
        This method retrieves a specific pipeline schedule from the database.

        Args:
            schedule_id (str): The ID of the pipeline schedule.

        Returns:
            PipelineScheduleModel | None: The pipeline schedule record or None if not found.
        """
        ...

    async def get_runs_by_schedule(self, schedule_id: str) -> list[PipelineRunModel]:
        """
        Get all pipeline runs associated with a specific schedule.
        This method retrieves all pipeline runs that are associated with the given schedule ID.

        Args:
            schedule_id (str): The ID of the pipeline schedule.

        Returns:
            list[PipelineRunModel]: A list of pipeline run records associated with the schedule.
        """
        ...

    async def get_run_history(self) -> list[PipelineRunModel]:
        """
        Get the history of all pipeline runs.
        This method retrieves all pipeline runs from the database.

        Returns:
            list[PipelineRunModel]: A list of all pipeline run records.
        """
        ...

    async def get_schedules(self) -> list[PipelineScheduleModel]:
        """
        Get all pipeline schedules from the database.
        This method retrieves all schedules from the database.

        Returns:
            list[PipelineScheduleModel]: A list of all pipeline schedule records.
        """
        ...

    async def create_schedule(
        self, schedule_id: str, hour: int, minute: int
    ) -> PipelineScheduleModel:
        """
        Create a new pipeline schedule record in the database.

        Args:
            schedule_id (str): The ID of the pipeline schedule.
            schedule_time (datetime): The time of the schedule.
            is_active (bool): Indicates whether the schedule is active.

        Returns:
            PipelineScheduleModel: The created pipeline schedule record.
        """
        ...

    async def get_latest_run(self) -> PipelineRunModel | None:
        """
        Get the latest pipeline run record from the database.
        This method retrieves the most recent pipeline run based on the start time.
        If no runs are found, it returns None.

        Returns:
            PipelineRunModel | None: The latest pipeline run record or None if no runs are found.
        """
        ...


@instrument_all_async(log_async_execution_time)
@dataclass(frozen=True, slots=True)
class PipelineRunPersistence(PipelineStorage):
    session_maker: async_sessionmaker[AsyncSession]

    async def create_schedule(
        self, schedule_id: str, hour: int, minute: int
    ) -> PipelineScheduleModel:
        async with self.session_maker() as session:
            await session.execute(update(PipelineScheduleModel).values(is_active=False))

            schedule = PipelineScheduleModel(
                schedule_id=schedule_id,
                hour=hour,
                minute=minute,
                is_active=True,
            )
            session.add(schedule)
            await session.commit()
            logger.info("Created new pipeline schedule", schedule_id=schedule_id)
            return schedule

    async def get_runs_by_schedule(self, schedule_id: str) -> list[PipelineRunModel]:
        async with self.session_maker() as session:
            stmt = select(PipelineRunModel).where(
                PipelineRunModel.associated_schedule == schedule_id
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_schedules(self) -> list[PipelineScheduleModel]:
        async with self.session_maker() as session:
            stmt = select(PipelineScheduleModel)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_run_history(self) -> list[PipelineRunModel]:
        async with self.session_maker() as session:
            stmt = select(PipelineRunModel)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create_pipeline_run(
        self,
        associated_schedule: str | None = None,
        success: bool = True,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        error_message: str | None = None,
    ) -> PipelineRunModel:
        async with self.session_maker() as session:
            pipeline_run = PipelineRunModel(
                start_time=start_time,
                associated_schedule=associated_schedule,
                success=success,
                end_time=end_time,
                error_message=error_message,
            )
            session.add(pipeline_run)
            await session.commit()
            logger.info("Created new pipeline run", run_id=pipeline_run.id)
            return pipeline_run

    async def get_latest_run(self) -> PipelineRunModel | None:
        """Get the latest pipeline run"""
        async with self.session_maker() as session:
            stmt = (
                select(PipelineRunModel)
                .order_by(PipelineRunModel.start_time.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_schedule(self, schedule_id: str) -> PipelineScheduleModel | None:
        async with self.session_maker() as session:
            stmt = select(PipelineScheduleModel).where(
                PipelineScheduleModel.id == schedule_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


def persistence_from_config(config: IngestionConfig) -> PipelineRunPersistence:
    """
    Factory method to create an instance of the pipeline storage service from a configuration object.

    Args:
        config (IngestionConfig): The configuration object to use for creating the service.

    Returns:
        PipelineRunPersistence: An instance of the PipelineRunPersistence class.
    """

    if "asyncpg" in config.db_connection_string:
        connection_args = {"server_settings": {"search_path": "public"}}
        engine = create_async_engine(
            config.db_connection_string,
            connect_args=connection_args,
        )
    else:
        engine = create_async_engine(config.db_connection_string)

    Session = async_sessionmaker(engine, expire_on_commit=False)
    return PipelineRunPersistence(session_maker=Session)
