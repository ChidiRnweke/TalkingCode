"""Unit tests for health controller."""

from dataclasses import dataclass

import pytest

from talkingcode.controllers.health_controller import HealthController
from talkingcode.domain.models import DependencyHealthStatus


@dataclass(slots=True)
class FakeHealthService:
    database_status: str = "ok"
    openrouter_status: str = "ok"
    github_status: str = "ok"

    async def check_database(self) -> DependencyHealthStatus:
        return DependencyHealthStatus(status=self.database_status)

    async def check_openrouter(self) -> DependencyHealthStatus:
        return DependencyHealthStatus(status=self.openrouter_status)

    async def check_github(self) -> DependencyHealthStatus:
        return DependencyHealthStatus(status=self.github_status)


@pytest.mark.asyncio
async def test_controller_returns_failed_when_dependency_failed() -> None:
    controller = HealthController(
        health_service=FakeHealthService(openrouter_status="failed")
    )
    result = await controller.check_health()
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_controller_returns_ok_when_dependency_skipped() -> None:
    controller = HealthController(health_service=FakeHealthService(github_status="skipped"))
    result = await controller.check_health()
    assert result.status == "ok"
