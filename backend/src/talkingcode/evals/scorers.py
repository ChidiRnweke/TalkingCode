"""Deterministic Phoenix evaluators for TalkingCode golden evals."""

from typing import Any


def _expectations(expected: dict[str, Any] | None) -> dict[str, Any]:
    return expected or {}


def _outputs(output: Any) -> dict[str, Any]:
    if isinstance(output, dict):
        return output
    return {"final_answer": str(output or "")}


def required_tools_called(output: Any, expected: dict[str, Any] | None) -> bool:
    """Checks that all tools required by the golden case were called."""
    required = set(_expectations(expected).get("required_tool_names", []))
    called = set(_outputs(output).get("tool_names", []))
    return required.issubset(called)


def tool_budget_met(output: Any, expected: dict[str, Any] | None) -> bool:
    """Checks that tool use stays within the golden case budget."""
    max_tool_calls = _expectations(expected).get("max_tool_calls")
    if max_tool_calls is None:
        return True
    return int(_outputs(output).get("tool_call_count", 0)) <= int(max_tool_calls)


def latency_budget_met(output: Any, expected: dict[str, Any] | None) -> bool:
    """Checks that the run stays within the golden case latency budget."""
    max_latency_ms = _expectations(expected).get("max_latency_ms")
    if max_latency_ms is None:
        return True
    latency_ms = _outputs(output).get("latency_ms")
    return latency_ms is not None and int(latency_ms) <= int(max_latency_ms)


def expected_sources_mentioned(output: Any, expected: dict[str, Any] | None) -> bool:
    """Checks that expected source path fragments are mentioned in the answer."""
    expected_paths = _expectations(expected).get("expected_source_paths", [])
    if not expected_paths:
        return True
    answer = _outputs(output).get("final_answer", "").lower()
    return all(path.lower() in answer for path in expected_paths)


def prohibited_claims_absent(output: Any, expected: dict[str, Any] | None) -> bool:
    """Checks that known unsupported claims are absent from the answer."""
    prohibited_claims = _expectations(expected).get("prohibited_claims", [])
    answer = _outputs(output).get("final_answer", "").lower()
    return not any(claim.lower() in answer for claim in prohibited_claims)


def tool_expectation_met(output: Any, expected: dict[str, Any] | None) -> bool:
    """Checks whether tools were used when the golden case requires them."""
    if not _expectations(expected).get("should_use_tools", False):
        return True
    return int(_outputs(output).get("tool_call_count", 0)) > 0


def deterministic_evaluators() -> dict[str, Any]:
    """Return the default deterministic evaluator set, keyed by evaluator name."""
    return {
        "talkingcode_required_tools_called": required_tools_called,
        "talkingcode_tool_budget_met": tool_budget_met,
        "talkingcode_latency_budget_met": latency_budget_met,
        "talkingcode_expected_sources_mentioned": expected_sources_mentioned,
        "talkingcode_prohibited_claims_absent": prohibited_claims_absent,
        "talkingcode_tool_expectation_met": tool_expectation_met,
    }
