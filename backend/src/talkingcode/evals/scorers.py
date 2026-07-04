"""Deterministic Phoenix evaluators for TalkingCode golden evals.

Each evaluator returns ``{"score", "label", "explanation"}`` so failures are
diagnosable per-example in the Phoenix experiments UI. Evaluators read the
trajectory record produced by ``talkingcode.evals.trajectory.run_agent_turn``.
"""

import re
from typing import Any

CITATION_RE = re.compile(r"\[(\d+)\]")
LEAKED_TAG_RE = re.compile(r"<tc-\w+|\[Source \d+\]")
CITING_TOOLS = {"search_github", "read_file"}


def _expectations(expected: dict[str, Any] | None) -> dict[str, Any]:
    return expected or {}


def _outputs(output: Any) -> dict[str, Any]:
    match output:
        case dict() as values:
            return values
        case _:
            return {"final_answer": str(output or "")}


def _result(passed: bool, explanation: str) -> dict[str, Any]:
    return {
        "score": 1.0 if passed else 0.0,
        "label": "pass" if passed else "fail",
        "explanation": explanation,
    }


def required_tools_called(
    output: Any, expected: dict[str, Any] | None
) -> dict[str, Any]:
    """Checks that all tools required by the golden case were called."""
    required = set(_expectations(expected).get("required_tool_names", []))
    called = set(_outputs(output).get("tool_names", []))
    missing = sorted(required - called)
    if missing:
        return _result(
            False, f"missing required tools {missing}; called {sorted(called)}"
        )
    return _result(True, f"all required tools called: {sorted(required)}")


def tool_expectation_met(
    output: Any, expected: dict[str, Any] | None
) -> dict[str, Any]:
    """Checks whether tools were used when the golden case requires them."""
    if not _expectations(expected).get("should_use_tools", False):
        return _result(True, "case does not require tool use")
    count = int(_outputs(output).get("tool_call_count", 0))
    return _result(count > 0, f"{count} tool call(s); at least 1 required")


def tool_budget_met(output: Any, expected: dict[str, Any] | None) -> dict[str, Any]:
    """Checks that tool use stays within the golden case budget."""
    max_tool_calls = _expectations(expected).get("max_tool_calls")
    count = int(_outputs(output).get("tool_call_count", 0))
    if max_tool_calls is None:
        return _result(True, f"{count} tool call(s); no budget set")
    return _result(
        count <= int(max_tool_calls),
        f"{count} tool call(s); budget {max_tool_calls}",
    )


def latency_budget_met(output: Any, expected: dict[str, Any] | None) -> dict[str, Any]:
    """Checks that the run stays within the golden case latency budget."""
    max_latency_ms = _expectations(expected).get("max_latency_ms")
    latency_ms = _outputs(output).get("latency_ms")
    if max_latency_ms is None:
        return _result(True, f"latency {latency_ms}ms; no budget set")
    passed = latency_ms is not None and int(latency_ms) <= int(max_latency_ms)
    return _result(passed, f"latency {latency_ms}ms; budget {max_latency_ms}ms")


def no_tool_errors(output: Any) -> dict[str, Any]:
    """Checks that no tool call returned an error."""
    errors = _outputs(output).get("tool_errors", [])
    if errors:
        return _result(False, f"tool errors: {errors}")
    return _result(True, "no tool errors")


def no_redundant_searches(output: Any) -> dict[str, Any]:
    """Checks that the agent never repeats an identical search query."""
    queries = [
        " ".join(str(query).lower().split())
        for query in _outputs(output).get("search_queries", [])
    ]
    duplicates = sorted({query for query in queries if queries.count(query) > 1})
    if duplicates:
        return _result(False, f"duplicate search queries: {duplicates}")
    return _result(True, f"{len(queries)} distinct search query(ies)")


def search_queries_on_topic(
    output: Any, expected: dict[str, Any] | None
) -> dict[str, Any]:
    """Checks that each expected term shows up in at least one search query."""
    terms = _expectations(expected).get("expected_query_terms", [])
    if not terms:
        return _result(True, "no expected query terms set")
    queries = [
        str(query).lower() for query in _outputs(output).get("search_queries", [])
    ]
    missing = [
        term for term in terms if not any(term.lower() in query for query in queries)
    ]
    if missing:
        return _result(False, f"no search query mentions {missing}; queries: {queries}")
    return _result(True, f"all expected terms {terms} appear in search queries")


def retrieval_hit(output: Any, expected: dict[str, Any] | None) -> dict[str, Any]:
    """Checks that expected paths were surfaced by tool results.

    A failure here with a passing agent points at retrieval/indexing; a pass
    here with a failing ``expected_sources_mentioned`` points at the agent
    ignoring evidence it retrieved.
    """
    expected_paths = _expectations(expected).get("expected_source_paths", [])
    if not expected_paths:
        return _result(True, "no expected source paths set")
    retrieved = [
        str(path).lower() for path in _outputs(output).get("retrieved_paths", [])
    ]
    missing = [
        path
        for path in expected_paths
        if not any(path.lower() in retrieved_path for retrieved_path in retrieved)
    ]
    if missing:
        return _result(False, f"never retrieved {missing}; retrieved {retrieved[:20]}")
    return _result(True, f"all expected paths retrieved: {expected_paths}")


def expected_sources_mentioned(
    output: Any, expected: dict[str, Any] | None
) -> dict[str, Any]:
    """Checks that expected source path fragments are mentioned in the answer."""
    expected_paths = _expectations(expected).get("expected_source_paths", [])
    if not expected_paths:
        return _result(True, "no expected source paths set")
    answer = str(_outputs(output).get("final_answer", "")).lower()
    missing = [path for path in expected_paths if path.lower() not in answer]
    if missing:
        return _result(False, f"answer does not mention {missing}")
    return _result(True, f"answer mentions all expected paths: {expected_paths}")


def prohibited_claims_absent(
    output: Any, expected: dict[str, Any] | None
) -> dict[str, Any]:
    """Checks that known unsupported claims are absent from the answer."""
    prohibited_claims = _expectations(expected).get("prohibited_claims", [])
    answer = str(_outputs(output).get("final_answer", "")).lower()
    found = [claim for claim in prohibited_claims if claim.lower() in answer]
    if found:
        return _result(False, f"answer contains prohibited claim(s): {found}")
    return _result(True, "no prohibited claims found")


def citations_present(output: Any) -> dict[str, Any]:
    """Checks that the answer carries [n] citations when evidence tools ran."""
    outputs = _outputs(output)
    citing_calls = [
        name for name in outputs.get("tool_names", []) if name in CITING_TOOLS
    ]
    answer = str(outputs.get("final_answer", ""))
    if not citing_calls:
        return _result(True, "no evidence tools called; citations not required")
    citations = CITATION_RE.findall(answer)
    if citations:
        return _result(True, f"answer carries {len(citations)} citation(s)")
    return _result(
        False,
        f"evidence tools ran ({sorted(set(citing_calls))}) but answer has no [n] citations",
    )


def citations_in_range(output: Any) -> dict[str, Any]:
    """Checks that no citation index exceeds the number of retrieved files."""
    outputs = _outputs(output)
    cited = [
        int(number)
        for number in CITATION_RE.findall(str(outputs.get("final_answer", "")))
    ]
    if not cited:
        return _result(True, "no citations in answer")
    available = len(set(outputs.get("retrieved_paths", [])))
    highest = max(cited)
    if highest > available:
        return _result(
            False,
            f"answer cites [{highest}] but only {available} unique file(s) were retrieved",
        )
    return _result(
        True, f"highest citation [{highest}] within {available} retrieved file(s)"
    )


def answer_has_no_leaked_tags(output: Any) -> dict[str, Any]:
    """Checks that internal stream tags and raw tool markup stay out of the answer."""
    answer = str(_outputs(output).get("final_answer", ""))
    leaked = sorted(set(LEAKED_TAG_RE.findall(answer)))
    if leaked:
        return _result(False, f"answer leaks internal markup: {leaked}")
    return _result(True, "no leaked markup")


def deterministic_evaluators() -> dict[str, Any]:
    """Return the default deterministic evaluator set, keyed by evaluator name."""
    return {
        "required_tools_called": required_tools_called,
        "tool_expectation_met": tool_expectation_met,
        "tool_budget_met": tool_budget_met,
        "latency_budget_met": latency_budget_met,
        "no_tool_errors": no_tool_errors,
        "no_redundant_searches": no_redundant_searches,
        "search_queries_on_topic": search_queries_on_topic,
        "retrieval_hit": retrieval_hit,
        "expected_sources_mentioned": expected_sources_mentioned,
        "prohibited_claims_absent": prohibited_claims_absent,
        "citations_present": citations_present,
        "citations_in_range": citations_in_range,
        "answer_has_no_leaked_tags": answer_has_no_leaked_tags,
    }
