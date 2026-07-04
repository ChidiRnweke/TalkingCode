from talkingcode.evals.scorers import (
    answer_has_no_leaked_tags,
    citations_in_range,
    citations_present,
    expected_sources_mentioned,
    latency_budget_met,
    no_redundant_searches,
    no_tool_errors,
    prohibited_claims_absent,
    required_tools_called,
    retrieval_hit,
    search_queries_on_topic,
    tool_budget_met,
    tool_expectation_met,
)


def test_required_tools_called_passes_when_required_tools_are_present() -> None:
    output = {"tool_names": ["search_github", "read_file"]}
    expected = {"required_tool_names": ["search_github"]}

    assert required_tools_called(output=output, expected=expected)["score"] == 1.0


def test_required_tools_called_fails_and_names_the_missing_tool() -> None:
    output = {"tool_names": ["search_github"]}
    expected = {"required_tool_names": ["read_file"]}

    result = required_tools_called(output=output, expected=expected)

    assert result["score"] == 0.0
    assert "read_file" in result["explanation"]


def test_tool_budget_met_fails_when_tool_count_exceeds_budget() -> None:
    output = {"tool_call_count": 4}
    expected = {"max_tool_calls": 3}

    assert tool_budget_met(output=output, expected=expected)["score"] == 0.0


def test_latency_budget_met_fails_when_latency_exceeds_budget() -> None:
    output = {"latency_ms": 61_000}
    expected = {"max_latency_ms": 60_000}

    assert latency_budget_met(output=output, expected=expected)["score"] == 0.0


def test_expected_sources_mentioned_requires_all_expected_fragments() -> None:
    output = {
        "final_answer": "See backend/src/talkingcode/services/agent/agent_service.py"
    }
    expected = {"expected_source_paths": ["agent_service.py"]}

    assert expected_sources_mentioned(output=output, expected=expected)["score"] == 1.0


def test_prohibited_claims_absent_fails_when_answer_contains_claim() -> None:
    output = {"final_answer": "This covers all projects."}
    expected = {"prohibited_claims": ["all projects"]}

    assert prohibited_claims_absent(output=output, expected=expected)["score"] == 0.0


def test_tool_expectation_met_requires_at_least_one_tool_call() -> None:
    output = {"tool_call_count": 0}
    expected = {"should_use_tools": True}

    assert tool_expectation_met(output=output, expected=expected)["score"] == 0.0


def test_no_tool_errors_fails_when_a_tool_returned_an_error() -> None:
    output = {"tool_errors": ["read_file: File missing.py not found"]}

    result = no_tool_errors(output=output)

    assert result["score"] == 0.0
    assert "missing.py" in result["explanation"]


def test_no_redundant_searches_fails_on_duplicate_queries() -> None:
    output = {"search_queries": ["svelte frontend", "Svelte  frontend"]}

    assert no_redundant_searches(output=output)["score"] == 0.0


def test_no_redundant_searches_passes_on_distinct_queries() -> None:
    output = {"search_queries": ["svelte frontend", "chat runtime"]}

    assert no_redundant_searches(output=output)["score"] == 1.0


def test_search_queries_on_topic_fails_when_term_never_searched() -> None:
    output = {"search_queries": ["chat runtime internals"]}
    expected = {"expected_query_terms": ["svelte"]}

    assert search_queries_on_topic(output=output, expected=expected)["score"] == 0.0


def test_retrieval_hit_fails_when_expected_path_never_retrieved() -> None:
    output = {"retrieved_paths": ["backend/src/talkingcode/factory.py"]}
    expected = {"expected_source_paths": ["agent_service.py"]}

    assert retrieval_hit(output=output, expected=expected)["score"] == 0.0


def test_retrieval_hit_passes_on_path_fragment_match() -> None:
    output = {
        "retrieved_paths": ["backend/src/talkingcode/services/agent/agent_service.py"]
    }
    expected = {"expected_source_paths": ["agent_service.py"]}

    assert retrieval_hit(output=output, expected=expected)["score"] == 1.0


def test_citations_present_fails_when_evidence_tools_ran_without_citations() -> None:
    output = {"tool_names": ["search_github"], "final_answer": "It uses Svelte."}

    assert citations_present(output=output)["score"] == 0.0


def test_citations_present_passes_when_answer_cites() -> None:
    output = {"tool_names": ["search_github"], "final_answer": "It uses Svelte [1]."}

    assert citations_present(output=output)["score"] == 1.0


def test_citations_in_range_fails_when_citation_exceeds_retrieved_files() -> None:
    output = {"final_answer": "See [9].", "retrieved_paths": ["a.py", "b.py"]}

    assert citations_in_range(output=output)["score"] == 0.0


def test_answer_has_no_leaked_tags_fails_on_internal_markup() -> None:
    output = {"final_answer": 'Done <tc-tool name="search_github"></tc-tool>'}

    assert answer_has_no_leaked_tags(output=output)["score"] == 0.0
