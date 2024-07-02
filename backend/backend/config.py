from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from dataclasses import dataclass
from openai import AsyncOpenAI
from typing import Self
from shared.env import env_var_or_default, env_var_or_throw
from sqlalchemy.ext.asyncio import create_async_engine
from logging import Logger


@dataclass(frozen=True)
class AppConfig:
    """
    This class is used to store the configuration for the application. It is obtained
    from the environment variables and passed to the application components that need
    it.

    You can instantiate it directly or use the `from_env` method to create an instance
    from the environment variables. The latter is the recommended way to create an
    instance. When certain environment variables are not set, it will log a warning if the
    application can still run without them, or raise an exception if the application
    cannot run without them.

    Attributes:
        embedding_model (str): The name of the text embedding model to use.
            Can be set with the `EMBEDDING_MODEL` environment variable.
        top_k (int): The number of top candidates to return from the model.
            Can be set with the `TOP_K` environment variable.
        chat_model (str): The name of the chat model to use.
            Can be set with the `CHAT_MODEL` environment variable.
        async_session (async_sessionmaker[AsyncSession]): The async session maker for the
            database.
            Can be set with the `ASYNC_DATABASE_URL` environment variable.
        system_prompt (str): The system prompt to use for the chat model.
            Can be set with the `SYSTEM_PROMPT` environment variable.
        openAI_client (AsyncOpenAI): The OpenAI client to use for making requests.
            Can be set with the `OPENAI_EMBEDDING_API_KEY` environment variable.
        max_spend (float): The maximum amount of money that can be spent in a day.
            Can be set with the `MAX_SPEND` environment variable.
    """

    embedding_model: str
    top_k: int
    chat_model: str
    async_session: async_sessionmaker[AsyncSession]
    system_prompt: str
    openAI_client: AsyncOpenAI
    max_spend: float

    @classmethod
    def from_env(cls, log: Logger | None = None) -> Self:
        """Create an instance of AppConfig from the environment variables.

        Args:
            log (Logger | None, optional): If provided, it logs whether or not the
                environment variables were found. Defaults to None.

        Returns:
           (AppConfig): The configuration object with the values from the environment
        """
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
    """Create an async session maker for the database.
    It uses the `ASYNC_DATABASE_URL` environment variable to connect to the database.


    Args:
        log (Logger | None, optional): If provided, it logs whether or not the
            connection string was found. Defaults to None.

    Returns:
        async_sessionmaker[AsyncSession]: The async session maker for the database.
    """
    conn_string = env_var_or_default(
        "ASYNC_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost/chatGITpt",
        log,
    )
    engine = create_async_engine(conn_string)
    return async_sessionmaker(engine, expire_on_commit=False)
