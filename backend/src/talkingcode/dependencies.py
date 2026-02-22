"""FastAPI dependencies."""
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from talkingcode.config import AppConfig
from talkingcode.factory import AppFactory
from talkingcode.repository.database import get_session as _get_session


async def get_config() -> AppConfig:
    """Get application config."""
    return AppConfig.from_env()


async def get_db_session(
    config: Annotated[AppConfig, Depends(get_config)],
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with _get_session(config.database_url) as session:
        yield session


async def get_factory(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> AppFactory:
    """Get application factory."""
    return AppFactory(session=session, config=config)


ConfigDep = Annotated[AppConfig, Depends(get_config)]
FactoryDep = Annotated[AppFactory, Depends(get_factory)]
