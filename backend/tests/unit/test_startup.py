from dataclasses import dataclass

import pytest

from talkingcode import startup


@dataclass(slots=True)
class StartupConfig:
    otel_exporter_endpoint: str = ""
    otel_service_name: str = "talkingcode-backend"
    otel_environment: str = "test"
    phoenix_project_name: str = "talkingcode"


class FakeInstrumentor:
    instrument_calls: list[dict] = []

    def instrument(self, **kwargs) -> None:
        FakeInstrumentor.instrument_calls.append(kwargs)


@pytest.fixture(autouse=True)
def reset_startup_state(monkeypatch) -> None:
    monkeypatch.setattr(startup, "_openai_agents_instrumented", False)
    FakeInstrumentor.instrument_calls = []
    monkeypatch.setattr(startup, "OpenAIAgentsInstrumentor", FakeInstrumentor)


def test_setup_openai_agents_tracing_instruments_the_global_provider() -> None:
    startup.setup_openai_agents_tracing()
    assert FakeInstrumentor.instrument_calls == [{}]


def test_setup_openai_agents_tracing_logs_enabled(monkeypatch) -> None:
    infos: list[tuple[str, dict]] = []

    def fake_info(event: str, **kwargs) -> None:
        infos.append((event, kwargs))

    monkeypatch.setattr(startup.logger, "info", fake_info)
    monkeypatch.setattr(startup, "OpenAIAgentsInstrumentor", FakeInstrumentor)

    startup.setup_openai_agents_tracing()

    assert infos == [("openai_agents_tracing.enabled", {})]


def test_setup_openai_agents_tracing_is_idempotent(monkeypatch) -> None:
    monkeypatch.setattr(startup, "OpenAIAgentsInstrumentor", FakeInstrumentor)

    startup.setup_openai_agents_tracing()
    startup.setup_openai_agents_tracing()

    assert len(FakeInstrumentor.instrument_calls) == 1


def test_setup_telemetry_if_enabled_passes_phoenix_project_to_configure(
    monkeypatch,
) -> None:
    configure_calls: list[dict] = []

    def fake_configure(**kwargs) -> None:
        configure_calls.append(kwargs)

    monkeypatch.setattr(startup, "configure_telemetry", fake_configure)

    config = StartupConfig(
        otel_exporter_endpoint="http://otel-collector:4317",
        otel_service_name="talkingcode-backend",
        otel_environment="test",
        phoenix_project_name="talkingcode-test",
    )

    startup.setup_telemetry_if_enabled(config)

    assert configure_calls == [
        {
            "endpoint": "http://otel-collector:4317",
            "service_name": "talkingcode-backend",
            "environment": "test",
            "phoenix_project": "talkingcode-test",
        }
    ]


def test_setup_telemetry_if_enabled_logs_disabled_when_endpoint_missing(
    monkeypatch,
) -> None:
    infos: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        startup, "configure_telemetry", lambda **kwargs: None
    )
    monkeypatch.setattr(startup.logger, "info", lambda event, **kw: infos.append((event, kw)))

    config = StartupConfig(otel_exporter_endpoint="")
    startup.setup_telemetry_if_enabled(config)

    assert infos == [("telemetry.disabled", {})]