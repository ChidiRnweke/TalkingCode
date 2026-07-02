from talkingcode.evals.scorers import (
    expected_sources_mentioned,
    latency_budget_met,
    prohibited_claims_absent,
    required_tools_called,
    tool_budget_met,
    tool_expectation_met,
)


def test_required_tools_called_passes_when_required_tools_are_present() -> None:
    outputs = {"tool_names": ["search_github", "read_file"]}
    expectations = {"required_tool_names": ["search_github"]}

    assert required_tools_called(outputs=outputs, expectations=expectations) is True


def test_required_tools_called_fails_when_required_tool_is_missing() -> None:
    outputs = {"tool_names": ["search_github"]}
    expectations = {"required_tool_names": ["read_file"]}

    assert required_tools_called(outputs=outputs, expectations=expectations) is False


def test_tool_budget_met_fails_when_tool_count_exceeds_budget() -> None:
    outputs = {"tool_call_count": 4}
    expectations = {"max_tool_calls": 3}

    assert tool_budget_met(outputs=outputs, expectations=expectations) is False


def test_latency_budget_met_fails_when_latency_exceeds_budget() -> None:
    outputs = {"latency_ms": 61_000}
    expectations = {"max_latency_ms": 60_000}

    assert latency_budget_met(outputs=outputs, expectations=expectations) is False


def test_expected_sources_mentioned_requires_all_expected_fragments() -> None:
    outputs = {"final_answer": "See backend/src/talkingcode/services/agent/agent_service.py"}
    expectations = {"expected_source_paths": ["agent_service.py"]}

    assert expected_sources_mentioned(outputs=outputs, expectations=expectations) is True


def test_prohibited_claims_absent_fails_when_answer_contains_claim() -> None:
    outputs = {"final_answer": "This covers all projects."}
    expectations = {"prohibited_claims": ["all projects"]}

    assert prohibited_claims_absent(outputs=outputs, expectations=expectations) is False


def test_tool_expectation_met_requires_at_least_one_tool_call() -> None:
    outputs = {"tool_call_count": 0}
    expectations = {"should_use_tools": True}

    assert tool_expectation_met(outputs=outputs, expectations=expectations) is False

