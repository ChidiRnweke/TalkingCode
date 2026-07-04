"""Health controller."""

import asyncio
from dataclasses import dataclass

from talkingcode.domain.models import HealthReport
from talkingcode.services.health_service import IHealthService


@dataclass(slots=True)
class HealthController:
    """Controller for dependency health checks."""

    health_service: IHealthService

    async def check_health(self) -> HealthReport:
        """Check all configured dependencies."""
        async with asyncio.TaskGroup() as task_group:
            database_task = task_group.create_task(self.health_service.check_database())
            openrouter_task = task_group.create_task(self.health_service.check_openrouter())
            github_task = task_group.create_task(self.health_service.check_github())

        dependencies = {
            "database": database_task.result(),
            "openrouter": openrouter_task.result(),
            "github": github_task.result(),
        }
        status = (
            "failed"
            if any(dependency.status == "failed" for dependency in dependencies.values())
            else "ok"
        )

        return HealthReport(status=status, dependencies=dependencies)
