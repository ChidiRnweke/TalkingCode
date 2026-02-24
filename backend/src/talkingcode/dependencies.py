"""FastAPI dependencies."""
import time
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from talkingcode.config import AppConfig
from talkingcode.factory import AppFactory
from talkingcode.repository.database import get_session as _get_session

logger = structlog.getLogger(__name__)

# ── Cached AppConfig singleton ──────────────────────────────────────
# AppConfig.from_env() may call Infisical for every secret.  We cache
# the result for 30 minutes so the Infisical API is hit at most once
# per TTL window, eliminating the 429 rate-limit errors.
_CONFIG_TTL_SECONDS = 30 * 60
_cached_config: AppConfig | None = None
_config_expires_at: float = 0.0


def _get_cached_config() -> AppConfig:
    """Return a cached AppConfig, rebuilding when TTL expires."""
    global _cached_config, _config_expires_at  # noqa: PLW0603

    now = time.monotonic()
    if _cached_config is not None and now < _config_expires_at:
        return _cached_config

    logger.info("config.loading", reason="cache_miss_or_expired")
    _cached_config = AppConfig.from_env()
    _config_expires_at = now + _CONFIG_TTL_SECONDS
    return _cached_config


async def get_config() -> AppConfig:
    """Get application config (cached with 30-min TTL)."""
    return _get_cached_config()


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
