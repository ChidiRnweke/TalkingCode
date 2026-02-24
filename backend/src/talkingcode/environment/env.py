import os
import time
import threading
from dataclasses import dataclass, field
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

# Default TTL for cached secrets: 30 minutes
_DEFAULT_SECRET_TTL_SECONDS = 30 * 60


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


@dataclass(slots=True)
class InfisicalSecretsBackend(SecretsBackend):
    """Infisical secrets backend with an in-memory TTL cache.

    Secrets are cached for ``ttl`` seconds (default 30 min) so that
    repeated reads (e.g. per-request ``AppConfig.from_env()``) never
    hit the Infisical API more than once per TTL window.
    """

    client: InfisicalClient
    project_id: str
    environment: str
    ttl: int = _DEFAULT_SECRET_TTL_SECONDS
    _cache: dict[str, tuple[str, float]] = field(default_factory=dict, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def read_secret(self, secret_name: str) -> str:
        now = time.monotonic()

        with self._lock:
            entry = self._cache.get(secret_name)
            if entry is not None:
                value, expires_at = entry
                if now < expires_at:
                    return value

        # Cache miss or expired — fetch from Infisical
        try:
            secret = self.client.getSecret(
                options=GetSecretOptions(
                    environment=self.environment,
                    project_id=self.project_id,
                    secret_name=secret_name,
                )
            )
            value = secret.secret_value
        except Exception as exc:  # noqa: BLE001
            raise SecretsNotFoundError(f"Secret {secret_name} not found") from exc

        with self._lock:
            self._cache[secret_name] = (value, now + self.ttl)
        logger.debug("secrets.cache.miss", secret=secret_name)
        return value

    def read_or_default(self, secret_name: str, default: str) -> str:
        return self.read_optional(secret_name) or default

    def read_optional(self, secret_name: str) -> str | None:
        try:
            return self.read_secret(secret_name)
        except Exception:
            return None

    @classmethod
    def from_env(cls, ttl: int = _DEFAULT_SECRET_TTL_SECONDS) -> Self:
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
            ttl=ttl,
        )


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
