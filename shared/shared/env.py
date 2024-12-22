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
from typing import Self

from shared.log import setup_custom_logger

logger = getLogger("app_logger")


@dataclass
class SecretsReader:
    client: InfisicalClient
    project_id: str
    environment: str

    def read_secret(self, secret_name: str) -> str:
        secret = self.client.getSecret(
            options=GetSecretOptions(
                environment=self.environment,
                project_id=self.project_id,
                secret_name=secret_name,
            )
        )
        return secret.secret_value

    @classmethod
    def from_env(cls) -> Self:
        client_id = get_env_or_raise("INFISICAL_CLIENT_ID")
        client_secret = get_env_or_raise("INFISICAL_CLIENT_SECRET")
        project_id = get_env_or_raise("INFISICAL_PROJECT_ID")
        environment = get_env_or_raise("INFISICAL_ENVIRONMENT")
        url = get_env_or_raise("INFISICAL_URL")

        auth = UniversalAuthMethod(client_id=client_id, client_secret=client_secret)
        auth_options = AuthenticationOptions(universal_auth=auth)
        client_settings = ClientSettings(auth=auth_options, site_url=url)

        return cls(
            client=InfisicalClient(client_settings),
            project_id=project_id,
            environment=environment,
        )


def setup_env(logger_name: str) -> None:
    logger = setup_custom_logger(logger_name)
    if not os.getenv("PRODUCTION"):
        logger.warning("Running in development mode")
        found = load_dotenv("../config/.env.secret.dev")
        if not found:
            logger.warning("No .env file found")


def env_var_or_default(var_name: str, default: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        logger.warning(
            f"{var_name} environment variable is not set. Fallback to default."
        )
        value = default
    return value


def get_env_or_raise(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        logger.error(f"{var_name} environment variable is not set. Cannot start app.")
        raise ValueError(
            f"{var_name} environment variable is not set. Cannot start app."
        )
    return value
