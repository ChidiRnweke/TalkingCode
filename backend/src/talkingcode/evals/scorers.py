"""Deterministic MLflow scorers for TalkingCode golden evals."""

from typing import Any

from mlflow.genai.scorers import scorer


def _expectations(expectations: dict[str, Any] | None) -> dict[str, Any]:
    return expectations or {}


def _outputs(outputs: Any) -> dict[str, Any]:
    if isinstance(outputs, dict):
        return outputs
    return {"final_answer": str(outputs or "")}


@scorer(
    name="talkingcode_required_tools_called",
    description="Checks that all tools required by the golden case were called.",
)
def required_tools_called(outputs: Any, expectations: dict[str, Any] | None) -> bool:
    expected = _expectations(expectations)
    required = set(expected.get("required_tool_names", []))
    called = set(_outputs(outputs).get("tool_names", []))
    return required.issubset(called)


@scorer(
    name="talkingcode_tool_budget_met",
    description="Checks that tool use stays within the golden case budget.",
)
def tool_budget_met(outputs: Any, expectations: dict[str, Any] | None) -> bool:
    expected = _expectations(expectations)
    max_tool_calls = expected.get("max_tool_calls")
    if max_tool_calls is None:
        return True
    return int(_outputs(outputs).get("tool_call_count", 0)) <= int(max_tool_calls)


@scorer(
    name="talkingcode_latency_budget_met",
    description="Checks that the run stays within the golden case latency budget.",
)
def latency_budget_met(outputs: Any, expectations: dict[str, Any] | None) -> bool:
    expected = _expectations(expectations)
    max_latency_ms = expected.get("max_latency_ms")
    if max_latency_ms is None:
        return True
    latency_ms = _outputs(outputs).get("latency_ms")
    return latency_ms is not None and int(latency_ms) <= int(max_latency_ms)


@scorer(
    name="talkingcode_expected_sources_mentioned",
    description="Checks that expected source path fragments are mentioned in the answer.",
)
def expected_sources_mentioned(
    outputs: Any, expectations: dict[str, Any] | None
) -> bool:
    expected_paths = _expectations(expectations).get("expected_source_paths", [])
    if not expected_paths:
        return True
    answer = _outputs(outputs).get("final_answer", "").lower()
    return all(path.lower() in answer for path in expected_paths)


@scorer(
    name="talkingcode_prohibited_claims_absent",
    description="Checks that known unsupported claims are absent from the answer.",
)
def prohibited_claims_absent(
    outputs: Any, expectations: dict[str, Any] | None
) -> bool:
    prohibited_claims = _expectations(expectations).get("prohibited_claims", [])
    answer = _outputs(outputs).get("final_answer", "").lower()
    return not any(claim.lower() in answer for claim in prohibited_claims)


@scorer(
    name="talkingcode_tool_expectation_met",
    description="Checks whether tools were used when the golden case requires them.",
)
def tool_expectation_met(outputs: Any, expectations: dict[str, Any] | None) -> bool:
    expected = _expectations(expectations)
    if not expected.get("should_use_tools", False):
        return True
    return int(_outputs(outputs).get("tool_call_count", 0)) > 0


def deterministic_scorers() -> list[Any]:
    """Return the default deterministic scorer set."""
    return [
        required_tools_called,
        tool_budget_met,
        latency_budget_met,
        expected_sources_mentioned,
        prohibited_claims_absent,
        tool_expectation_met,
    ]

