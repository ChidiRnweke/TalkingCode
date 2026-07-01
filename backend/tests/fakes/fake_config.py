"""Fake application configuration for testing."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class FakeAppConfig:
    """Hand-rolled fake AppConfig for tests.  No mocks, no HTTP."""

    ingestion_api_key: str = "secret-key"
    database_url: str = "postgresql+asyncpg://fake:fake@localhost/fake"
    openrouter_api_key: str = "test-key"
    github_token: str = "test-token"
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
    mlflow_tracking_uri: str = ""
    mlflow_experiment_name: str = "test"
    otel_exporter_endpoint: str = ""
    otel_service_name: str = "test"
    otel_environment: str = "test"
