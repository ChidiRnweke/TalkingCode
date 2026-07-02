from dataclasses import dataclass

import pytest

from talkingcode import startup


@dataclass(slots=True)
class StartupConfig:
    phoenix_collector_endpoint: str = ""
    phoenix_api_key: str = ""
    phoenix_project_name: str = "test"


class FakeLogger:
    def __init__(self) -> None:
        self.infos: list[tuple[str, dict]] = []
        self.warnings: list[tuple[str, dict]] = []
        self.errors: list[tuple[str, dict]] = []

    def info(self, event: str, **kwargs) -> None:
        self.infos.append((event, kwargs))

    def warning(self, event: str, **kwargs) -> None:
        self.warnings.append((event, kwargs))

    def error(self, event: str, **kwargs) -> None:
        self.errors.append((event, kwargs))


class FakeInstrumentor:
    instrument_calls: list[dict] = []

    def instrument(self, **kwargs) -> None:
        FakeInstrumentor.instrument_calls.append(kwargs)


@pytest.fixture(autouse=True)
def reset_phoenix_state(monkeypatch) -> None:
    monkeypatch.setattr(startup, "_phoenix_configured", False)
    FakeInstrumentor.instrument_calls = []


def test_configure_phoenix_tracing_warns_when_endpoint_is_missing(
    monkeypatch,
) -> None:
    register_calls: list[dict] = []
    fake_logger = FakeLogger()

    monkeypatch.setattr(startup.logger, "warning", fake_logger.warning)
    monkeypatch.setattr(
        startup, "register", lambda **kwargs: register_calls.append(kwargs)
    )

    startup.configure_phoenix_tracing(StartupConfig(phoenix_collector_endpoint=""))

    assert register_calls == []
    assert fake_logger.warnings == [
        ("phoenix.tracing.disabled", {"reason": "missing_collector_endpoint"})
    ]


def test_configure_phoenix_tracing_instruments_openai_agents_when_endpoint_is_set(
    monkeypatch,
) -> None:
    register_calls: list[dict] = []
    fake_logger = FakeLogger()
    sentinel_provider = object()
    config = StartupConfig(
        phoenix_collector_endpoint="https://phoenix.example.com/",
        phoenix_api_key="test-api-key",
        phoenix_project_name="talkingcode-test",
    )

    def fake_register(**kwargs) -> object:
        register_calls.append(kwargs)
        return sentinel_provider

    monkeypatch.setattr(startup.logger, "info", fake_logger.info)
    monkeypatch.setattr(startup, "register", fake_register)
    monkeypatch.setattr(startup, "OpenAIAgentsInstrumentor", FakeInstrumentor)

    startup.configure_phoenix_tracing(config)

    assert len(register_calls) == 1
    register_kwargs = register_calls[0]
    assert register_kwargs["endpoint"] == "https://phoenix.example.com/v1/traces"
    assert register_kwargs["project_name"] == "talkingcode-test"
    assert register_kwargs["api_key"] == "test-api-key"
    assert register_kwargs["set_global_tracer_provider"] is False
    assert FakeInstrumentor.instrument_calls == [
        {"tracer_provider": sentinel_provider}
    ]
    assert fake_logger.infos == [
        (
            "phoenix.openai_agents_tracing.enabled",
            {
                "endpoint": "https://phoenix.example.com/",
                "project_name": "talkingcode-test",
            },
        )
    ]


def test_configure_phoenix_tracing_logs_error_when_api_key_missing(
    monkeypatch,
) -> None:
    fake_logger = FakeLogger()
    config = StartupConfig(
        phoenix_collector_endpoint="https://phoenix.example.com/",
        phoenix_api_key="",
    )

    monkeypatch.setattr(startup.logger, "info", fake_logger.info)
    monkeypatch.setattr(startup.logger, "error", fake_logger.error)
    monkeypatch.setattr(startup, "register", lambda **kwargs: object())
    monkeypatch.setattr(startup, "OpenAIAgentsInstrumentor", FakeInstrumentor)

    startup.configure_phoenix_tracing(config)

    assert fake_logger.errors == [
        (
            "phoenix.tracing.misconfigured",
            {
                "reason": "missing_api_key",
                "endpoint": "https://phoenix.example.com/",
            },
        )
    ]


def test_configure_phoenix_tracing_is_idempotent(monkeypatch) -> None:
    register_calls: list[dict] = []
    config = StartupConfig(phoenix_collector_endpoint="https://phoenix.example.com")

    def fake_register(**kwargs) -> object:
        register_calls.append(kwargs)
        return object()

    monkeypatch.setattr(startup, "register", fake_register)
    monkeypatch.setattr(startup, "OpenAIAgentsInstrumentor", FakeInstrumentor)

    startup.configure_phoenix_tracing(config)
    startup.configure_phoenix_tracing(config)

    assert len(register_calls) == 1
    assert len(FakeInstrumentor.instrument_calls) == 1
