import os
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
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

# Retry a transient Infisical fetch failure (e.g. a cold-start network race)
# before giving up, so a boot-time hiccup doesn't get cached as "no secret"
# for the lifetime of the process.
_INFISICAL_FETCH_RETRIES = 3
_INFISICAL_FETCH_BACKOFF_SECONDS = (0.5, 1.0, 2.0)


class SecretsNotFoundError(Exception):
    pass


class SecretsBackend(Protocol):
    def read_secret(self, secret_name: str) -> str: ...
    def read_or_default(self, secret_name: str, default: str) -> str: ...
    def read_optional(self, secret_name: str) -> str | None: ...


@dataclass(frozen=True, slots=True)
class EnvSecretsBackend(SecretsBackend):
    def read_secret(self, secret_name: str) -> str:
        value = os.environ.get(secret_name)
        if value is None:
            raise SecretsNotFoundError(f"Missing env var: {secret_name}")
        return value

    def read_or_default(self, secret_name: str, default: str) -> str:
        value = os.environ.get(secret_name)
        if value is None:
            logger.warning("env.default.used", var=secret_name)
            return default
        return value

    def read_optional(self, secret_name: str) -> str | None:
        return os.environ.get(secret_name)


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

        # Cache miss or expired — fetch from Infisical, retrying transient
        # failures (e.g. a cold-start network race) before giving up.
        last_exc: Exception | None = None
        value: str | None = None
        for attempt in range(_INFISICAL_FETCH_RETRIES):
            try:
                secret = self.client.getSecret(
                    options=GetSecretOptions(
                        environment=self.environment,
                        project_id=self.project_id,
                        secret_name=secret_name,
                    )
                )
                value = secret.secret_value
                last_exc = None
                break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < _INFISICAL_FETCH_RETRIES - 1:
                    logger.warning(
                        "secrets.fetch.retry",
                        secret=secret_name,
                        attempt=attempt + 1,
                        error=str(exc),
                    )
                    time.sleep(_INFISICAL_FETCH_BACKOFF_SECONDS[attempt])

        if last_exc is not None:
            raise SecretsNotFoundError(f"Secret {secret_name} not found") from last_exc
        assert value is not None

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
        env = EnvSecretsBackend()
        client_id = env.read_secret("INFISICAL_CLIENT_ID")
        client_secret = env.read_secret("INFISICAL_CLIENT_SECRET")
        project_id = env.read_secret("INFISICAL_PROJECT_ID")
        environment = env.read_secret("INFISICAL_ENVIRONMENT")
        url = env.read_secret("INFISICAL_URL")

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
        # env.py is at backend/src/talkingcode/environment/env.py
        # Resolve 4 parents up to get the backend/ directory
        _backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        load_dotenv(_backend_dir / ".env")
        enabled = os.environ.get("INFISICAL_ENABLED")
        if enabled:
            logger.info("secrets.backend.infisical.enabled")
            return cls(backend=InfisicalSecretsBackend.from_env())
        logger.info("secrets.backend.env.enabled")
        return cls(backend=EnvSecretsBackend())



