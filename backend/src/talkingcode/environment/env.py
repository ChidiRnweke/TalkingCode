import os
from dataclasses import dataclass
from typing import Protocol, Self

from dotenv import load_dotenv
from infisical_client import (
    AuthenticationOptions,
    ClientSettings,
    GetSecretOptions,
    InfisicalClient,
    UniversalAuthMethod,
)
import structlog

logger = structlog.getLogger("talkingcode")


class SecretsNotFoundError(Exception):
    pass


class SecretsBackend(Protocol):
    def read_secret(self, secret_name: str) -> str: ...
    def read_or_default(self, secret_name: str, default: str) -> str: ...
    def read_optional(self, secret_name: str) -> str | None: ...


@dataclass(frozen=True, slots=True)
class EnvSecretsBackend(SecretsBackend):
    def read_secret(self, secret_name: str) -> str:
        return get_env_or_raise(secret_name)

    def read_or_default(self, secret_name: str, default: str) -> str:
        return env_var_or_default(secret_name, default)

    def read_optional(self, secret_name: str) -> str | None:
        return os.getenv(secret_name)


@dataclass(frozen=True, slots=True)
class InfisicalSecretsBackend(SecretsBackend):
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
        except Exception as exc:  # noqa: BLE001
            raise SecretsNotFoundError(f"Secret {secret_name} not found") from exc

    def read_or_default(self, secret_name: str, default: str) -> str:
        return self.read_optional(secret_name) or default

    def read_optional(self, secret_name: str) -> str | None:
        try:
            return self.read_secret(secret_name)
        except Exception:
            return None

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
        client = InfisicalClient(client_settings)
        return cls(client=client, project_id=project_id, environment=environment)


@dataclass(frozen=True, slots=True)
class SecretsReader:
    backend: SecretsBackend

    def read_secret(self, secret_name: str) -> str:
        return self.backend.read_secret(secret_name)

    def read_or_default(self, secret_name: str, default: str) -> str:
        return self.backend.read_or_default(secret_name, default)

    def read_optional(self, secret_name: str) -> str | None:
        return self.backend.read_optional(secret_name)

    @classmethod
    def from_env(cls) -> Self:
        load_dotenv()
        enabled = os.getenv("INFISICAL_ENABLED")
        if enabled:
            logger.info("secrets.backend.infisical.enabled")
            return cls(backend=InfisicalSecretsBackend.from_env())
        logger.info("secrets.backend.env.enabled")
        return cls(backend=EnvSecretsBackend())


def env_var_or_default(var_name: str, default: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        logger.warning("env.default.used", var=var_name)
        return default
    return value


def get_env_or_raise(var_name: str) -> str:
    value = os.getenv(var_name)
    if value is None:
        logger.error("env.required.missing", var=var_name)
        raise SecretsNotFoundError(f"Missing env var: {var_name}")
    return value
