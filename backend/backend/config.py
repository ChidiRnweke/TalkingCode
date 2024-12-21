from logging import getLogger
from dotenv import load_dotenv
import os
from dataclasses import dataclass
from infisical_client import (
    ClientSettings,
    InfisicalClient,
    GetSecretOptions,
    AuthenticationOptions,
    UniversalAuthMethod,
)
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from shared.telemetry import configure_telemetry as _configure_telemetry

logger = getLogger("backend_logger")


class AppStartupError(Exception):
    pass


def get_env_or_raise(env_var: str) -> str:
    value = os.getenv(env_var)
    if value is None:
        err_msg = f"Environment variable {env_var} not set"
        logger.error(err_msg)
        raise AppStartupError(err_msg)
    return value


def configure_telemetry(logger_name: str):
    telemetry_endpoint = get_env_or_raise("TELEMETRY_ENDPOINT")
    _configure_telemetry(telemetry_endpoint, logger_name)


@dataclass
class AppConfig:
    embedding_model: str
    top_k: int
    chat_model: str
    async_session: async_sessionmaker[AsyncSession]
    system_prompt: str
    openAI_client: AsyncOpenAI
    max_spend: float
    migrations_connection_string: str

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
        client_id = get_env_or_raise("INFISICAL_CLIENT_ID")
        client_secret = get_env_or_raise("INFISICAL_CLIENT_SECRET")
        project_id = get_env_or_raise("INFISICAL_PROJECT_ID")
        environment = get_env_or_raise("INFISICAL_ENVIRONMENT")
        url = get_env_or_raise("INFISICAL_URL")

        auth = UniversalAuthMethod(client_id=client_id, client_secret=client_secret)
        auth_options = AuthenticationOptions(universal_auth=auth)
        client_settings = ClientSettings(auth=auth_options, site_url=url)
        try:
            client = InfisicalClient(client_settings)
            conn_str = cls._read_secret(
                secret_name="EMBEDDING_MODEL",
                client=client,
                project_id=project_id,
                environment=environment,
            )

            migrations_conn_str = cls._read_secret(
                secret_name="MIGRATIONS_DATABASE_CONNECTION_STRING",
                client=client,
                project_id=project_id,
                environment=environment,
            )

            embedding_model = cls._read_secret(
                secret_name="EMBEDDING_MODEL",
                client=client,
                project_id=project_id,
                environment=environment,
            )

            top_k = int(
                cls._read_secret(
                    secret_name="TOP_K",
                    client=client,
                    project_id=project_id,
                    environment=environment,
                )
            )

            chat_model = cls._read_secret(
                secret_name="CHAT_MODEL",
                client=client,
                project_id=project_id,
                environment=environment,
            )

            system_prompt = cls._read_secret(
                secret_name="SYSTEM_PROMPT",
                client=client,
                project_id=project_id,
                environment=environment,
            )

            max_spend = float(
                cls._read_secret(
                    secret_name="MAX_SPEND",
                    client=client,
                    project_id=project_id,
                    environment=environment,
                )
            )

            openai_api_key = cls._read_secret(
                secret_name="OPENAI_API_KEY",
                client=client,
                project_id=project_id,
                environment=environment,
            )

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
            migrations_connection_string=migrations_conn_str,
        )

    @staticmethod
    def _read_secret(
        secret_name: str,
        client: InfisicalClient,
        project_id: str,
        environment: str,
    ) -> str:
        secret = client.getSecret(
            options=GetSecretOptions(
                environment=environment,
                project_id=project_id,
                secret_name=secret_name,
            )
        )
        return secret.secret_value


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
