from talkingcode.evals.scorers import (
    expected_sources_mentioned,
    latency_budget_met,
    prohibited_claims_absent,
    required_tools_called,
    tool_budget_met,
    tool_expectation_met,
)


def test_required_tools_called_passes_when_required_tools_are_present() -> None:
    output = {"tool_names": ["search_github", "read_file"]}
    expected = {"required_tool_names": ["search_github"]}

    assert required_tools_called(output=output, expected=expected) is True


def test_required_tools_called_fails_when_required_tool_is_missing() -> None:
    output = {"tool_names": ["search_github"]}
    expected = {"required_tool_names": ["read_file"]}

    assert required_tools_called(output=output, expected=expected) is False


def test_tool_budget_met_fails_when_tool_count_exceeds_budget() -> None:
    output = {"tool_call_count": 4}
    expected = {"max_tool_calls": 3}

    assert tool_budget_met(output=output, expected=expected) is False


def test_latency_budget_met_fails_when_latency_exceeds_budget() -> None:
    output = {"latency_ms": 61_000}
    expected = {"max_latency_ms": 60_000}

    assert latency_budget_met(output=output, expected=expected) is False


def test_expected_sources_mentioned_requires_all_expected_fragments() -> None:
    output = {"final_answer": "See backend/src/talkingcode/services/agent/agent_service.py"}
    expected = {"expected_source_paths": ["agent_service.py"]}

    assert expected_sources_mentioned(output=output, expected=expected) is True


def test_prohibited_claims_absent_fails_when_answer_contains_claim() -> None:
    output = {"final_answer": "This covers all projects."}
    expected = {"prohibited_claims": ["all projects"]}

    assert prohibited_claims_absent(output=output, expected=expected) is False


def test_tool_expectation_met_requires_at_least_one_tool_call() -> None:
    output = {"tool_call_count": 0}
    expected = {"should_use_tools": True}

    assert tool_expectation_met(output=output, expected=expected) is False
