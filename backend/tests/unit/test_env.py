"""Tests for the Infisical-backed secrets reader."""

from dataclasses import dataclass

import pytest

from talkingcode.environment import env


@dataclass(slots=True)
class FakeSecret:
    secret_value: str


class FakeInfisicalClient:
    def __init__(self, values: list[FakeSecret | Exception]) -> None:
        self._values = values
        self.calls = 0

    def getSecret(self, options):  # noqa: N802 - matches infisical_client's API
        result = self._values[self.calls]
        self.calls += 1
        if isinstance(result, Exception):
            raise result
        return result


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch) -> None:
    monkeypatch.setattr(env.time, "sleep", lambda _seconds: None)


def make_backend(client: FakeInfisicalClient) -> env.InfisicalSecretsBackend:
    return env.InfisicalSecretsBackend(
        client=client,
        project_id="proj",
        environment="prod",
    )


def test_read_secret_returns_value_on_first_try() -> None:
    client = FakeInfisicalClient([FakeSecret("my-value")])
    backend = make_backend(client)

    assert backend.read_secret("PHOENIX_API_KEY") == "my-value"


def test_read_secret_calls_client_once_on_first_try() -> None:
    client = FakeInfisicalClient([FakeSecret("my-value")])
    backend = make_backend(client)

    backend.read_secret("PHOENIX_API_KEY")
    assert client.calls == 1


def test_read_secret_retries_then_succeeds() -> None:
    client = FakeInfisicalClient(
        [RuntimeError("network blip"), RuntimeError("network blip"), FakeSecret("my-value")]
    )
    backend = make_backend(client)

    assert backend.read_secret("PHOENIX_API_KEY") == "my-value"


def test_read_secret_calls_client_for_each_retry() -> None:
    client = FakeInfisicalClient(
        [RuntimeError("network blip"), RuntimeError("network blip"), FakeSecret("my-value")]
    )
    backend = make_backend(client)

    backend.read_secret("PHOENIX_API_KEY")
    assert client.calls == 3


def test_read_secret_raises_after_exhausting_retries() -> None:
    client = FakeInfisicalClient(
        [RuntimeError("network blip"), RuntimeError("network blip"), RuntimeError("network blip")]
    )
    backend = make_backend(client)
    raised = False

    try:
        backend.read_secret("PHOENIX_API_KEY")
    except env.SecretsNotFoundError:
        raised = True

    assert raised is True


def test_read_secret_calls_client_for_all_exhausted_retries() -> None:
    client = FakeInfisicalClient(
        [RuntimeError("network blip"), RuntimeError("network blip"), RuntimeError("network blip")]
    )
    backend = make_backend(client)

    with pytest.raises(env.SecretsNotFoundError):
        backend.read_secret("PHOENIX_API_KEY")
    assert client.calls == 3


def test_read_secret_uses_cached_value() -> None:
    client = FakeInfisicalClient([FakeSecret("my-value")])
    backend = make_backend(client)

    backend.read_secret("PHOENIX_API_KEY")
    assert backend.read_secret("PHOENIX_API_KEY") == "my-value"


def test_read_secret_cache_avoids_second_client_call() -> None:
    client = FakeInfisicalClient([FakeSecret("my-value")])
    backend = make_backend(client)

    backend.read_secret("PHOENIX_API_KEY")
    backend.read_secret("PHOENIX_API_KEY")
    assert client.calls == 1


def test_read_or_default_falls_back_after_exhausting_retries() -> None:
    client = FakeInfisicalClient(
        [RuntimeError("network blip"), RuntimeError("network blip"), RuntimeError("network blip")]
    )
    backend = make_backend(client)

    assert backend.read_or_default("PHOENIX_API_KEY", "fallback") == "fallback"
