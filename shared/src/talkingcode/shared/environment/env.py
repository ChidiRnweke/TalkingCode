import os
from dataclasses import dataclass
from logging import getLogger
from typing import Protocol, Self

from dotenv import load_dotenv
from infisical_client import (
    AuthenticationOptions,
    ClientSettings,
    GetSecretOptions,
    InfisicalClient,
    UniversalAuthMethod,
)

logger = getLogger("app_logger")


class SecretsNotFoundError(Exception):
    pass


class SecretsBackend(Protocol):
    """
    A backend for reading secrets. Implementations of this protocol should provide
    methods to read secrets from a secret store.

    It is here to abstract the implementation details of reading secrets from different
    sources, such as environment variables or a secret management service.
    """

    def read_secret(self, secret_name: str) -> str:
        """
        Read a secret from the backend. If the secret is not found, raise an exception.

        Args:
            secret_name (str): The name of the secret to read.

        Returns:
            str: The value of the secret.

        Raises:
            SecretsNotFoundError: If the secret is not found.
        """

        ...

    def read_or_default(self, secret_name: str, default: str) -> str:
        """
        Read a secret from the backend. If the secret is not found, return the default value.

        Args:
            secret_name (str): The name of the secret to read.
            default (str): The default value to return if the secret is not found.

        Returns:
            str: The value of the secret or the default value.
        """

        ...

    def read_optional(self, secret_name: str) -> str | None:
        """
        Read a secret from the backend. If the secret is not found, return None.

        Args:
            secret_name (str): The name of the secret to read.

        Returns:
            str | None: The value of the secret or None if the secret is not found.
        """

        ...


@dataclass(frozen=True, slots=True)
class EnvSecretsBackend(SecretsBackend):
    """
    A backend for reading secrets from environment variables.
    """

    def read_secret(self, secret_name: str) -> str:
        return get_env_or_raise(secret_name)

    def read_or_default(self, secret_name: str, default: str) -> str:
        return env_var_or_default(secret_name, default)

    def read_optional(self, secret_name: str) -> str | None:
        return os.getenv(secret_name)


@dataclass(frozen=True, slots=True)
class InfisicalSecretsBackend(SecretsBackend):
    """
    A backend for reading secrets from Infisical. Requires infisical server
    to be running for the client to connect to.


    Args:
        client (InfisicalClient): The Infisical client to use.
        project_id (str): The ID of the project to read secrets from.
        environment (str): The environment to read secrets from.
    """

    client: InfisicalClient
    project_id: str
    environment: str

    def read_secret(self, secret_name: str) -> str:
        try:
            secret = self.client.getSecret(
                options=GetSecretOptions(
                    environment=self.environment,
                    project_id=self.project_id,
                    secret_name=secret_name,
                )
            )
            return secret.secret_value
        except Exception as e:
            raise SecretsNotFoundError(f"Secret {secret_name} not found.") from e

    def read_or_default(self, secret_name: str, default: str) -> str:
        return self.read_optional(secret_name) or default

    def read_optional(self, secret_name: str) -> str | None:
        try:
            return self.read_secret(secret_name)
        except Exception:
            return None

    @classmethod
    def from_env(cls) -> Self:
        """
        Create an InfisicalSecretsBackend instance using the environment variables.
        It reads the INFISICAL_CLIENT_ID, INFISICAL_CLIENT_SECRET, INFISICAL_PROJECT_ID,
        INFISICAL_ENVIRONMENT, and INFISICAL_URL environment variables. If any of these
        variables are not set, a `SecretsNotFoundError` is raised.


        Returns:
            Self: The InfisicalSecretsBackend instance.
        """
        client_id = get_env_or_raise("INFISICAL_CLIENT_ID")
        client_secret = get_env_or_raise("INFISICAL_CLIENT_SECRET")
        project_id = get_env_or_raise("INFISICAL_PROJECT_ID")
        environment = get_env_or_raise("INFISICAL_ENVIRONMENT")
        url = get_env_or_raise("INFISICAL_URL")

        auth = UniversalAuthMethod(client_id=client_id, client_secret=client_secret)
        auth_options = AuthenticationOptions(universal_auth=auth)
        client_settings = ClientSettings(auth=auth_options, site_url=url)
        client = InfisicalClient(client_settings)

        return cls(
            client=client,
            project_id=project_id,
            environment=environment,
        )


@dataclass(frozen=True, slots=True)
class SecretsReader:
    """
    A class for reading secrets from a backend. It provides methods to read secrets
    from the backend, with different behaviors for when the secret is not found.


    Args:
        backend (SecretsBackend): The backend to use for reading secrets.
    """

    backend: SecretsBackend

    def read_secret(self, secret_name: str) -> str:
        """
        Read a secret from the backend. If the secret is not found, raise an exception.

        Args:
            secret_name (str): The name of the secret to read.

        Returns:
            str: The value of the secret.

        Raises:
            SecretsNotFoundError: If the secret is not found.
        """
        return self.backend.read_secret(secret_name)

    def read_or_default(self, secret_name: str, default: str) -> str:
        """
        Read a secret from the backend. If the secret is not found, return the default value.

        Args:
            secret_name (str): The name of the secret to read.
            default (str): The default value to return if the secret is not found.

        Returns:
            str: The value of the secret or the default value.
        """
        return self.backend.read_or_default(secret_name, default)

    def read_optional(self, secret_name: str) -> str | None:
        """
        Read a secret from the backend. If the secret is not found, return None.

        Args:
            secret_name (str): The name of the secret to read.

        Returns:
            str | None: The value of the secret or None if the secret is not found.
        """
        return self.backend.read_optional(secret_name)

    @classmethod
    def from_env(cls) -> Self:
        """
        Create a SecretsReader instance using the environment variables.
        The right backend is chosen based on the INFISICAL_ENABLED environment variable.

        Returns:
            Self: The SecretsReader instance.
        """
        load_dotenv()
        infisical_enabled = os.getenv("INFISICAL_ENABLED")
        if infisical_enabled:
            logger.info("Using Infisical as secrets backend")
            return cls(backend=InfisicalSecretsBackend.from_env())
        else:
            logger.info("Using environment variables as secrets backend")
            return cls(backend=EnvSecretsBackend())


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
        raise SecretsNotFoundError(
            f"{var_name} environment variable is not set. Cannot start app."
        )
    return value
