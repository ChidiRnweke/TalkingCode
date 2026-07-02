from talkingcode.evals.dataset import load_golden_records


def test_load_golden_records_uses_question_input_key() -> None:
    records = load_golden_records()

    assert "question" in records[0]["inputs"]


def test_load_golden_records_preserves_case_id_in_expectations() -> None:
    records = load_golden_records()

    assert records[0]["expectations"]["case_id"] == "repo-discovery-svelte"


def test_load_golden_records_preserves_category_tag() -> None:
    records = load_golden_records()

    assert records[0]["tags"]["category"] == "repo_discovery"

