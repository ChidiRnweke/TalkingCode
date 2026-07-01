from dataclasses import dataclass

from talkingcode import startup


@dataclass(slots=True)
class StartupConfig:
    mlflow_tracking_uri: str = ""
    mlflow_experiment_name: str = "test"


class FakeLogger:
    def __init__(self) -> None:
        self.infos: list[tuple[str, dict]] = []
        self.warnings: list[tuple[str, dict]] = []

    def info(self, event: str, **kwargs) -> None:
        self.infos.append((event, kwargs))

    def warning(self, event: str, **kwargs) -> None:
        self.warnings.append((event, kwargs))


def test_configure_mlflow_tracing_warns_when_tracking_uri_is_missing(
    monkeypatch,
) -> None:
    autolog_calls = 0
    fake_logger = FakeLogger()

    def fake_autolog() -> None:
        nonlocal autolog_calls
        autolog_calls += 1

    monkeypatch.setattr(startup.logger, "warning", fake_logger.warning)
    monkeypatch.setattr(startup.mlflow.openai, "autolog", fake_autolog)

    startup.configure_mlflow_tracing(StartupConfig(mlflow_tracking_uri=""))

    assert autolog_calls == 0
    assert fake_logger.warnings == [
        ("mlflow.tracing.disabled", {"reason": "missing_tracking_uri"})
    ]


def test_configure_mlflow_tracing_instruments_openai_agents_when_server_is_set(
    monkeypatch,
) -> None:
    calls: list[tuple[str, object]] = []
    fake_logger = FakeLogger()
    config = StartupConfig(
        mlflow_tracking_uri="http://localhost:5000",
        mlflow_experiment_name="talkingcode-test",
    )

    monkeypatch.setattr(startup.logger, "info", fake_logger.info)
    monkeypatch.setattr(
        startup.mlflow,
        "set_tracking_uri",
        lambda uri: calls.append(("set_tracking_uri", uri)),
    )
    monkeypatch.setattr(
        startup.mlflow,
        "set_experiment",
        lambda *, experiment_name: calls.append(("set_experiment", experiment_name)),
    )
    monkeypatch.setattr(
        startup.mlflow.openai,
        "autolog",
        lambda: calls.append(("autolog", None)),
    )

    startup.configure_mlflow_tracing(config)

    assert calls == [
        ("set_tracking_uri", "http://localhost:5000"),
        ("set_experiment", "talkingcode-test"),
        ("autolog", None),
    ]
    assert fake_logger.infos == [
        (
            "mlflow.openai_agents_tracing.enabled",
            {
                "tracking_uri": "http://localhost:5000",
                "experiment_name": "talkingcode-test",
            },
        )
    ]
