"""Unit tests for health routes."""

from dataclasses import dataclass

import pytest

from talkingcode.domain.models import DependencyHealthStatus, HealthReport
from talkingcode.routes.health_routes import health_check


@dataclass(slots=True)
class FakeHealthController:
    status: str

    async def check_health(self) -> HealthReport:
        return HealthReport(
            status=self.status,
            dependencies={"database": DependencyHealthStatus(status=self.status)},
        )


@dataclass(slots=True)
class FakeFactory:
    controller: FakeHealthController

    def get_health_controller(self) -> FakeHealthController:
        return self.controller


@pytest.mark.asyncio
async def test_route_returns_500_when_report_failed() -> None:
    response = await health_check(
        factory=FakeFactory(controller=FakeHealthController(status="failed"))
    )
    assert response.status_code == 500


@pytest.mark.asyncio
async def test_route_returns_200_when_report_ok() -> None:
    response = await health_check(
        factory=FakeFactory(controller=FakeHealthController(status="ok"))
    )
    assert response.status_code == 200
