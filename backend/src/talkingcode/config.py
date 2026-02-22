"""Application configuration."""
from dataclasses import dataclass
from typing import Self

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Database
    database_url: str = "postgresql+asyncpg://talkingcode:talkingcode@localhost:5432/talkingcode"
    
    # LLM APIs
    openrouter_api_key: str = ""
    github_token: str = ""
    ingestion_api_key: str = ""
    
    # App Config
    environment: str = "development"
    log_level: str = "INFO"
    default_model: str = "anthropic/claude-3.5-sonnet"
    fallback_model: str = "google/gemini-3-flash"
    
    # Planner Settings
    max_iterations: int = 8
    max_tools_per_turn: int = 3
    default_tool_timeout: int = 15
    
    # Embeddings
    embedding_model: str = "openai/text-embedding-3-large"
    embedding_dimensions: int = 3072

    # Intent extraction (cheap model for query classification)
    intent_extraction_model: str = "deepseek/deepseek-v3.2"

    # Curated model list
    curated_models: str = "google/gemini-3-flash-preview,deepseek/deepseek-v3.2,moonshotai/kimi-k2.5,qwen/qwen3.5-plus-02-15,z-ai/glm-4.7,openai/gpt-5.1-codex-mini"
    default_chat_model: str = "google/gemini-3-flash-preview"
    
    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        return self.database_url


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
        settings = Settings()
        return cls(
            database_url=settings.database_url_async,
            openrouter_api_key=settings.openrouter_api_key,
            github_token=settings.github_token,
            ingestion_api_key=settings.ingestion_api_key,
            environment=settings.environment,
            log_level=settings.log_level,
            default_model=settings.default_model,
            fallback_model=settings.fallback_model,
            max_iterations=settings.max_iterations,
            max_tools_per_turn=settings.max_tools_per_turn,
            default_tool_timeout=settings.default_tool_timeout,
            embedding_model=settings.embedding_model,
            embedding_dimensions=settings.embedding_dimensions,
            intent_extraction_model=settings.intent_extraction_model,
            curated_models=settings.curated_models,
            default_chat_model=settings.default_chat_model,
        )
