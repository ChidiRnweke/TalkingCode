from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from dataclasses import dataclass
from openai import AsyncOpenAI
from typing import Self
from shared.env import env_var_or_default, env_var_or_throw
from sqlalchemy.ext.asyncio import create_async_engine
from logging import Logger


@dataclass(frozen=True)
class AppConfig:
    embedding_model: str
    top_k: int
    chat_model: str
    async_session: async_sessionmaker[AsyncSession]
    system_prompt: str
    openAI_client: AsyncOpenAI
    max_spend: float

    @classmethod
    def from_env(cls, log: Logger | None = None) -> Self:
        Session = configure_async_session_maker(log)
        embedding_model = env_var_or_default(
            "EMBEDDING_MODEL", "text-embedding-3-large", log
        )
        chat_model = env_var_or_default("CHAT_MODEL", "gpt-4o", log)
        open_ai_key = env_var_or_throw("OPENAI_EMBEDDING_API_KEY", log)
        top_k = int(env_var_or_default("TOP_K", "5", log))
        max_spend = float(env_var_or_default("MAX_SPEND", "1.5", log))
        openAI_client = AsyncOpenAI(api_key=open_ai_key)
        system_prompt = env_var_or_default(
            "SYSTEM_PROMPT",
            "You are a helpful assistant.",
            log,
        )

        config = cls(
            embedding_model=embedding_model,
            chat_model=chat_model,
            async_session=Session,
            openAI_client=openAI_client,
            top_k=top_k,
            system_prompt=system_prompt,
            max_spend=max_spend,
        )
        return config


def configure_async_session_maker(
    log: Logger | None = None,
) -> async_sessionmaker[AsyncSession]:
    conn_string = env_var_or_default(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost/chatGITpt",
        log,
    )
    engine = create_async_engine(conn_string)
    return async_sessionmaker(engine, expire_on_commit=False)
