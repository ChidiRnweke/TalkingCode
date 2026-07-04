from dataclasses import dataclass

import pytest

from talkingcode import startup


@dataclass(slots=True)
class StartupConfig:
    otel_exporter_endpoint: str = ""
    otel_service_name: str = "talkingcode-backend"
    otel_environment: str = "test"
    phoenix_project_name: str = "talkingcode"


@pytest.fixture(autouse=True)
def reset_startup_state(monkeypatch) -> None:
    register_calls: list[dict] = []
    monkeypatch.setattr(
        startup, "register", lambda **kwargs: register_calls.append(kwargs)
    )
    monkeypatch.setattr(startup, "_register_calls", register_calls, raising=False)


def test_setup_phoenix_tracing_registers_with_collector_endpoint(monkeypatch) -> None:
    register_calls: list[dict] = []
    fake_provider = object()

    def fake_register(**kwargs):
        register_calls.append(kwargs)
        return fake_provider

    monkeypatch.setattr(startup, "register", fake_register)
    provider_calls: list[object] = []
    monkeypatch.setattr(startup, "set_phoenix_tracer_provider", provider_calls.append)

    config = StartupConfig(
        otel_exporter_endpoint="http://otel-collector:4317",
        phoenix_project_name="talkingcode-test",
    )

    startup.setup_phoenix_tracing(config)

    assert provider_calls == [fake_provider]
    assert len(register_calls) == 1
    call = register_calls[0]
    assert call["endpoint"] == "http://otel-collector:4318/v1/traces"
    assert call["protocol"] == "http/protobuf"
    assert call["project_name"] == "talkingcode-test"
    assert call["set_global_tracer_provider"] is False
    assert call["auto_instrument"] is True
    assert call["batch"] is True
    assert call["verbose"] is False
    assert "api_key" not in call


def test_setup_phoenix_tracing_skips_when_endpoint_missing(monkeypatch) -> None:
    register_calls: list[dict] = []
    monkeypatch.setattr(
        startup, "register", lambda **kwargs: register_calls.append(kwargs)
    )
    warnings: list[tuple[str, dict]] = []
    monkeypatch.setattr(startup.logger, "warning", lambda event, **kw: warnings.append((event, kw)))

    config = StartupConfig(otel_exporter_endpoint="")
    startup.setup_phoenix_tracing(config)

    assert register_calls == []
    assert warnings == [("phoenix.tracing.disabled", {"reason": "missing_otel_endpoint"})]


def test_setup_telemetry_if_enabled_passes_endpoint_to_configure(monkeypatch) -> None:
    configure_calls: list[dict] = []

    def fake_configure(**kwargs) -> None:
        configure_calls.append(kwargs)

    monkeypatch.setattr(startup, "configure_telemetry", fake_configure)

    config = StartupConfig(
        otel_exporter_endpoint="http://otel-collector:4317",
        otel_service_name="talkingcode-backend",
        otel_environment="test",
    )

    startup.setup_telemetry_if_enabled(config)

    assert configure_calls == [
        {
            "endpoint": "http://otel-collector:4317",
            "service_name": "talkingcode-backend",
            "environment": "test",
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