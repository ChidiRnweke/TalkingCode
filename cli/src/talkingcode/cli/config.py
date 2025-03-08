from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class DatabaseType(str, Enum):
    sqlite = "sqlite"
    postgres = "postgres"


class QdrantMode(str, Enum):
    local = "local"
    server = "server"


@dataclass
class CLIConfig:
    github_token: str
    openai_key: str
    db_type: DatabaseType
    db_url: Optional[str]
    qdrant_mode: QdrantMode
    qdrant_url: Optional[str]
    config_dir: Path = Path.home() / ".talkingcode"

    def create_env_content(self) -> list[str]:
        """Generate environment variable content"""
        env_content = [
            f"GITHUB_TOKEN={self.github_token}",
            f"OPENAI_API_KEY={self.openai_key}",
            "EMBEDDING_MODEL=text-embedding-3-large",
            "CHAT_MODEL=gpt-4",
            "TOP_K=5",
            "MAX_SPEND=10.0",
            'SYSTEM_PROMPT="You are a helpful AI assistant that answers questions about code."',
            "METADATA_ENRICHMENT_MODEL=gpt-4",
            'KEYWORD_IDENTIFIER_PROMPT="Identify the key technical concepts in this code."',
        ]

        if self.db_type == DatabaseType.postgres:
            env_content.append(f"ASYNC_DATABASE_URL={self.db_url}")
        else:
            db_path = self.config_dir / "talkingcode.db"
            env_content.append(f"ASYNC_DATABASE_URL=sqlite+aiosqlite:///{db_path}")

        if self.qdrant_mode == QdrantMode.server:
            env_content.append(f"QDRANT_SERVER_URL={self.qdrant_url}")
        else:
            qdrant_path = self.config_dir / "qdrant"
            env_content.append(f"QDRANT_LOCAL_STORAGE_PATH={qdrant_path}")

        return env_content

    def save(self) -> None:
        """Save configuration to .env file"""
        self.config_dir.mkdir(exist_ok=True)
        env_path = self.config_dir / ".env"
        env_content = self.create_env_content()
        env_path.write_text("\n".join(env_content))
