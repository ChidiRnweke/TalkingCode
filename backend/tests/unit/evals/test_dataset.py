from talkingcode.evals.dataset import load_golden_records


def test_load_golden_records_uses_question_input_key() -> None:
    records = load_golden_records()

    assert "question" in records[0]["input"]


def test_load_golden_records_preserves_case_id_in_expectations() -> None:
    records = load_golden_records()

    assert records[0]["output"]["case_id"] == "repo-discovery-svelte"


def test_load_golden_records_uses_case_id_as_stable_example_id() -> None:
    records = load_golden_records()

    assert records[0]["id"] == "repo-discovery-svelte"


def test_load_golden_records_uses_category_as_split() -> None:
    records = load_golden_records()

    assert records[0]["splits"] == ["repo_discovery"]
    assert records[0]["metadata"]["category"] == "repo_discovery"
