"""Unit tests for dependency health checks."""

from dataclasses import dataclass, field
from typing import Any

import pytest

from talkingcode.services.health_service import (
    GITHUB_RATE_LIMIT_URL,
    GITHUB_USER_URL,
    OPENROUTER_KEY_URL,
    HealthService,
)


@dataclass(slots=True, frozen=True)
class FakeAppConfig:
    database_url: str = "postgresql+asyncpg://fake:fake@localhost/fake"
    openrouter_api_key: str = "test-key"
    github_token: str = "test-token"
    ingestion_api_key: str = "secret-key"
    environment: str = "test"
    log_level: str = "DEBUG"
    default_model: str = "test-model"
    fallback_model: str = "fallback-model"
    max_iterations: int = 8
    max_tools_per_turn: int = 3
    default_tool_timeout: int = 15
    embedding_model: str = "test-embedding"
    embedding_dimensions: int = 1536
    intent_extraction_model: str = "test-intent"
    curated_models: str = ""
    default_chat_model: str = "test-chat"
    phoenix_collector_endpoint: str = ""
    phoenix_api_key: str = ""
    phoenix_project_name: str = "test"
    otel_exporter_endpoint: str = ""
    otel_service_name: str = "test"
    otel_environment: str = "test"


@dataclass(slots=True)
class FakeHealthRepository:
    error: Exception | None = None

    async def ping_database(self) -> None:
        if self.error:
            raise self.error


@dataclass(slots=True)
class FakeExternalHealthClient:
    responses: dict[str, tuple[int, dict[str, Any]]] = field(default_factory=dict)
    error: Exception | None = None

    async def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        if self.error:
            raise self.error
        return self.responses[url]


def make_service(
    repository: FakeHealthRepository | None = None,
    client: FakeExternalHealthClient | None = None,
    config: FakeAppConfig | None = None,
) -> HealthService:
    return HealthService(
        health_repository=repository or FakeHealthRepository(),
        external_client=client or FakeExternalHealthClient(),
        config=config or FakeAppConfig(),
    )


@pytest.mark.asyncio
async def test_database_success_returns_ok() -> None:
    result = await make_service().check_database()
    assert result.status == "ok"


@pytest.mark.asyncio
async def test_database_error_returns_failed() -> None:
    service = make_service(repository=FakeHealthRepository(error=RuntimeError("down")))
    result = await service.check_database()
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_openrouter_remaining_limit_returns_ok() -> None:
    service = make_service(
        client=FakeExternalHealthClient(
            responses={
                OPENROUTER_KEY_URL: (
                    200,
                    {"data": {"limit": 100, "limit_remaining": 1, "limit_reset": "monthly", "usage": 99}},
                )
            }
        )
    )
    result = await service.check_openrouter()
    assert result.status == "ok"


@pytest.mark.asyncio
async def test_openrouter_unlimited_limit_returns_ok() -> None:
    service = make_service(
        client=FakeExternalHealthClient(
            responses={OPENROUTER_KEY_URL: (200, {"data": {"limit_remaining": None}})}
        )
    )
    result = await service.check_openrouter()
    assert result.status == "ok"


@pytest.mark.asyncio
async def test_openrouter_empty_limit_returns_failed() -> None:
    service = make_service(
        client=FakeExternalHealthClient(
            responses={OPENROUTER_KEY_URL: (200, {"data": {"limit_remaining": 0}})}
        )
    )
    result = await service.check_openrouter()
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_openrouter_unauthorised_returns_failed() -> None:
    service = make_service(
        client=FakeExternalHealthClient(responses={OPENROUTER_KEY_URL: (401, {})})
    )
    result = await service.check_openrouter()
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_github_absent_token_returns_skipped() -> None:
    service = make_service(config=FakeAppConfig(github_token=""))
    result = await service.check_github()
    assert result.status == "skipped"


@pytest.mark.asyncio
async def test_github_valid_token_returns_ok() -> None:
    service = make_service(
        client=FakeExternalHealthClient(
            responses={
                GITHUB_USER_URL: (200, {"login": "octocat"}),
                GITHUB_RATE_LIMIT_URL: (
                    200,
                    {"resources": {"core": {"remaining": 4999, "limit": 5000}}},
                ),
            }
        )
    )
    result = await service.check_github()
    assert result.status == "ok"


@pytest.mark.asyncio
async def test_github_unauthorised_returns_failed() -> None:
    service = make_service(
        client=FakeExternalHealthClient(responses={GITHUB_USER_URL: (401, {})})
    )
    result = await service.check_github()
    assert result.status == "failed"


@pytest.mark.asyncio
async def test_github_rate_limit_error_returns_failed() -> None:
    service = make_service(
        client=FakeExternalHealthClient(
            responses={
                GITHUB_USER_URL: (200, {"login": "octocat"}),
                GITHUB_RATE_LIMIT_URL: (500, {}),
            }
        )
    )
    result = await service.check_github()
    assert result.status == "failed"
