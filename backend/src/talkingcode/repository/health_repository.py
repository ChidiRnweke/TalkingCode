"""Health check repository."""

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class IHealthRepository(Protocol):
    """Protocol for infrastructure health checks."""

    async def ping_database(self) -> None:
        """Verify database reachability."""
        ...


@dataclass(slots=True)
class HealthRepository:
    """Repository for infrastructure health checks."""

    session: AsyncSession

    async def ping_database(self) -> None:
        """Verify database reachability."""
        await self.session.execute(text("SELECT 1"))
