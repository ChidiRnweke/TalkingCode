"""Unit tests for ingestion authentication dependency.

Tests the require_ingestion_api_key FastAPI dependency directly
(no app spinning, no mocks).
"""

import pytest

from talkingcode.dependencies import require_ingestion_api_key
from talkingcode.errors import UnauthorisedError
from tests.fakes.fake_config import FakeAppConfig


# ---------------------------------------------------------------------------
# Missing / absent key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_raises_when_no_key_configured() -> None:
    """When config has empty ingestion_api_key, any request raises UnauthorisedError."""
    config = FakeAppConfig(ingestion_api_key="")

    with pytest.raises(UnauthorisedError):
        await require_ingestion_api_key(config=config, x_api_key="anything")


@pytest.mark.asyncio
async def test_auth_raises_when_no_key_provided() -> None:
    """When no key is supplied (neither header nor query), raise UnauthorisedError."""
    config = FakeAppConfig(ingestion_api_key="secret-key")

    with pytest.raises(UnauthorisedError):
        await require_ingestion_api_key(config=config)


@pytest.mark.asyncio
async def test_auth_raises_with_both_key_sources_absent() -> None:
    """Both x_api_key=None and api_key=None should raise UnauthorisedError."""
    config = FakeAppConfig(ingestion_api_key="secret-key")

    with pytest.raises(UnauthorisedError):
        await require_ingestion_api_key(config=config, x_api_key=None, api_key=None)


# ---------------------------------------------------------------------------
# Wrong key — header
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_raises_with_wrong_header_key() -> None:
    """A wrong X-API-Key header raises UnauthorisedError."""
    config = FakeAppConfig(ingestion_api_key="secret-key")

    with pytest.raises(UnauthorisedError):
        await require_ingestion_api_key(config=config, x_api_key="wrong")


# ---------------------------------------------------------------------------
# Wrong key — query parameter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_raises_with_wrong_query_key() -> None:
    """A wrong api_key query parameter raises UnauthorisedError."""
    config = FakeAppConfig(ingestion_api_key="secret-key")

    with pytest.raises(UnauthorisedError):
        await require_ingestion_api_key(config=config, api_key="wrong")


# ---------------------------------------------------------------------------
# Valid key — header
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_accepts_valid_header_key() -> None:
    """A correct X-API-Key header returns None (auth passes)."""
    config = FakeAppConfig(ingestion_api_key="secret-key")

    result = await require_ingestion_api_key(config=config, x_api_key="secret-key")

    assert result is None


# ---------------------------------------------------------------------------
# Valid key — query parameter
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_accepts_valid_query_key() -> None:
    """A correct api_key query parameter returns None (auth passes)."""
    config = FakeAppConfig(ingestion_api_key="secret-key")

    result = await require_ingestion_api_key(config=config, api_key="secret-key")

    assert result is None


# ---------------------------------------------------------------------------
# Header takes precedence over query (when both provided)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auth_accepts_when_header_valid_ignores_query() -> None:
    """With a valid header, auth passes even if query has a wrong key."""
    config = FakeAppConfig(ingestion_api_key="secret-key")

    result = await require_ingestion_api_key(
        config=config, x_api_key="secret-key", api_key="wrong"
    )

    assert result is None
