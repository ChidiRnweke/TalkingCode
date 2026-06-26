"""Application configuration."""

from dataclasses import dataclass
from typing import Self

from talkingcode.environment.env import SecretsReader


@dataclass(slots=True, frozen=True)
class AppConfig:
    """Runtime application configuration."""

    database_url: str
    openrouter_api_key: str
    github_token: str
    ingestion_api_key: str
    environment: str
    log_level: str
    default_model: str
    fallback_model: str
    max_iterations: int
    max_tools_per_turn: int
    default_tool_timeout: int
    embedding_model: str
    embedding_dimensions: int
    intent_extraction_model: str
    curated_models: str
    default_chat_model: str

    @classmethod
    def from_env(cls) -> Self:
        """Create configuration from environment."""
        reader = SecretsReader.from_env()
        return cls(
            database_url=reader.read_secret("DATABASE_URL"),
            openrouter_api_key=reader.read_secret("OPENROUTER_API_KEY"),
            github_token=reader.read_or_default("GITHUB_TOKEN", ""),
            ingestion_api_key=reader.read_secret("INGESTION_API_KEY"),
            environment=reader.read_or_default("ENVIRONMENT", "development"),
            log_level=reader.read_or_default("LOG_LEVEL", "INFO"),
            default_model=reader.read_or_default("DEFAULT_MODEL", "anthropic/claude-3.5-sonnet"),
            fallback_model=reader.read_or_default("FALLBACK_MODEL", "google/gemini-3-flash"),
            max_iterations=int(reader.read_or_default("MAX_ITERATIONS", "16")),
            max_tools_per_turn=int(reader.read_or_default("MAX_TOOLS_PER_TURN", "3")),
            default_tool_timeout=int(reader.read_or_default("DEFAULT_TOOL_TIMEOUT", "15")),
            embedding_model=reader.read_or_default("EMBEDDING_MODEL", "openai/text-embedding-3-large"),
            embedding_dimensions=int(reader.read_or_default("EMBEDDING_DIMENSIONS", "3072")),
            intent_extraction_model=reader.read_or_default("INTENT_EXTRACTION_MODEL", "deepseek/deepseek-v3.2"),
            curated_models=reader.read_or_default("CURATED_MODELS", ""),
            default_chat_model=reader.read_or_default("DEFAULT_CHAT_MODEL", "google/gemini-3-flash-preview"),
        )
