"""Dependency health checks."""

from dataclasses import dataclass
from typing import Any, Protocol

import httpx
import structlog

from talkingcode.config import AppConfig
from talkingcode.domain.models import DependencyHealthStatus
from talkingcode.repository.health_repository import IHealthRepository

logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

OPENROUTER_KEY_URL = "https://openrouter.ai/api/v1/key"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_RATE_LIMIT_URL = "https://api.github.com/rate_limit"


class IExternalHealthClient(Protocol):
    """Protocol for health-check HTTP calls."""

    async def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        """Return HTTP status and parsed JSON body."""
        ...


@dataclass(slots=True)
class ExternalHealthClient:
    """HTTP client for external dependency health probes."""

    timeout_seconds: float = 5.0

    async def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        """Return HTTP status and parsed JSON body."""
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url, headers=headers)
            body = response.json() if response.content else {}
            return response.status_code, body


class IHealthService(Protocol):
    """Protocol for dependency health checks."""

    async def check_database(self) -> DependencyHealthStatus:
        """Check database reachability."""
        ...

    async def check_openrouter(self) -> DependencyHealthStatus:
        """Check OpenRouter API key and credit limit status."""
        ...

    async def check_github(self) -> DependencyHealthStatus:
        """Check GitHub token validity and rate limit status."""
        ...


@dataclass(slots=True)
class HealthService:
    """Health check service for runtime dependencies."""

    health_repository: IHealthRepository
    config: AppConfig
    external_client: IExternalHealthClient

    async def check_database(self) -> DependencyHealthStatus:
        """Check database reachability."""
        try:
            await self.health_repository.ping_database()
            return DependencyHealthStatus(status="ok")
        except Exception as exc:  # noqa: BLE001
            logger.error("health.database.failed", error=str(exc))
            return DependencyHealthStatus(status="failed", message="Database check failed")

    async def check_openrouter(self) -> DependencyHealthStatus:
        """Check OpenRouter API key and credit limit status."""
        try:
            status_code, body = await self.external_client.get_json(
                OPENROUTER_KEY_URL,
                headers={"Authorization": f"Bearer {self.config.openrouter_api_key}"},
            )
            if status_code != 200:
                return self._failed_openrouter(f"OpenRouter returned HTTP {status_code}")

            match body.get("data"):
                case dict() as data:
                    pass
                case _:
                    return self._failed_openrouter("OpenRouter returned an invalid response")
            limit_remaining = data.get("limit_remaining")
            match limit_remaining:
                case int() | float() as remaining if remaining <= 0:
                    return self._failed_openrouter("OpenRouter key has no remaining credits")

            return DependencyHealthStatus(
                status="ok",
                details={
                    "limit": data.get("limit"),
                    "limit_remaining": limit_remaining,
                    "limit_reset": data.get("limit_reset"),
                    "usage": data.get("usage"),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("health.openrouter.failed", error=str(exc))
            return DependencyHealthStatus(status="failed", message="OpenRouter check failed")

    async def check_github(self) -> DependencyHealthStatus:
        """Check GitHub token validity and rate limit status."""
        if not self.config.github_token:
            return DependencyHealthStatus(
                status="skipped",
                message="GITHUB_TOKEN is not configured",
            )

        try:
            headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.config.github_token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            user_status_code, user_body = await self.external_client.get_json(
                GITHUB_USER_URL,
                headers=headers,
            )
            if user_status_code == 401:
                return self._failed_github("GitHub token is invalid, expired, or revoked")
            if user_status_code != 200:
                return self._failed_github(f"GitHub user check returned HTTP {user_status_code}")

            rate_status_code, rate_body = await self.external_client.get_json(
                GITHUB_RATE_LIMIT_URL,
                headers=headers,
            )
            if rate_status_code != 200:
                return self._failed_github(f"GitHub rate limit check returned HTTP {rate_status_code}")

            match rate_body.get("resources"):
                case {"core": dict() as core_rate}:
                    pass
                case _:
                    core_rate = {}
            return DependencyHealthStatus(
                status="ok",
                details={
                    "login": user_body.get("login"),
                    "rate_limit_remaining": core_rate.get("remaining"),
                    "rate_limit_limit": core_rate.get("limit"),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("health.github.failed", error=str(exc))
            return DependencyHealthStatus(status="failed", message="GitHub check failed")

    def _failed_openrouter(self, message: str) -> DependencyHealthStatus:
        logger.error("health.openrouter.failed", error=message)
        return DependencyHealthStatus(status="failed", message=message)

    def _failed_github(self, message: str) -> DependencyHealthStatus:
        logger.error("health.github.failed", error=message)
        return DependencyHealthStatus(status="failed", message=message)
