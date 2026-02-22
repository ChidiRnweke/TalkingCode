"""FastAPI dependencies."""
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
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


async def require_ingestion_api_key(
    config: Annotated[AppConfig, Depends(get_config)],
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    api_key: Annotated[str | None, Query(alias="api_key")] = None,
) -> None:
    """Require valid ingestion API key.
    
    Checks X-API-Key header first, then api_key query parameter.
    """
    effective_key = x_api_key or api_key
    print(f"DEBUG: Config: {config}")
    print(f"DEBUG: Ingestion Key: '{config.ingestion_api_key}'")
    
    if not config.ingestion_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ingestion API key not configured",
        )
        
    if effective_key != config.ingestion_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ingestion API key",
        )


ConfigDep = Annotated[AppConfig, Depends(get_config)]
FactoryDep = Annotated[AppFactory, Depends(get_factory)]
IngestionAuthDep = Annotated[None, Depends(require_ingestion_api_key)]
