from logging import getLogger
from dotenv import load_dotenv
import os
from dataclasses import dataclass

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from shared.telemetry import configure_telemetry as _configure_telemetry
from shared.env import SecretsReader

logger = getLogger("app_logger")


class AppStartupError(Exception):
    pass


def get_env_or_raise(env_var: str) -> str:
    value = os.getenv(env_var)
    if value is None:
        err_msg = f"Environment variable {env_var} not set"
        logger.error(err_msg)
        raise AppStartupError(err_msg)
    return value


def configure_telemetry():
    telemetry_endpoint = get_env_or_raise("TELEMETRY_ENDPOINT")
    _configure_telemetry(telemetry_endpoint)


@dataclass
class AppConfig:
    embedding_model: str
    top_k: int
    chat_model: str
    async_session: async_sessionmaker[AsyncSession]
    system_prompt: str
    openAI_client: AsyncOpenAI
    max_spend: float

    @classmethod
    def from_config(cls) -> "AppConfig":
        load_dotenv()
        if os.getenv("ENV") == "LOCAL":
            conf = cls._from_env()
        else:
            conf = cls._from_vault()
        return conf

    @classmethod
    def _from_env(cls) -> "AppConfig":
        raise NotImplementedError("This method is not implemented yet")

    @classmethod
    def _from_vault(cls) -> "AppConfig":
        reader = SecretsReader.from_env()

        try:
            conn_str = reader.read_secret(secret_name="EMBEDDING_MODEL")
            embedding_model = reader.read_secret(secret_name="EMBEDDING_MODEL")
            top_k = int(reader.read_secret(secret_name="TOP_K"))
            chat_model = reader.read_secret(secret_name="CHAT_MODEL")
            system_prompt = reader.read_secret(secret_name="SYSTEM_PROMPT")
            max_spend = float(reader.read_secret(secret_name="MAX_SPEND"))
            openai_api_key = reader.read_secret(secret_name="OPENAI_API_KEY")
            openAI_client = AsyncOpenAI(api_key=openai_api_key)

            session = configure_async_session_maker(conn_str)

        except Exception as e:
            raise AppStartupError(f"Error reading secret from infisical: {e}") from e
        return cls(
            embedding_model=embedding_model,
            top_k=top_k,
            chat_model=chat_model,
            async_session=session,
            system_prompt=system_prompt,
            openAI_client=openAI_client,
            max_spend=max_spend,
        )


def configure_async_session_maker(conn_str: str) -> async_sessionmaker[AsyncSession]:
    """Create an async session maker for the database.
    It uses the `ASYNC_DATABASE_URL` environment variable to connect to the database.


    Args:
        log (Logger | None, optional): If provided, it logs whether or not the
            connection string was found. Defaults to None.

    Returns:
        async_sessionmaker[AsyncSession]: The async session maker for the database.
    """

    engine = create_async_engine(conn_str)
    return async_sessionmaker(engine, expire_on_commit=False)
