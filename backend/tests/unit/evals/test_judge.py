import pytest

from talkingcode.evals.judge import parse_judgement


def test_parse_judgement_reads_clean_json() -> None:
    label, explanation = parse_judgement(
        '{"label": "on_track", "explanation": "Focused searches."}'
    )

    assert label == "on_track"
    assert explanation == "Focused searches."


def test_parse_judgement_reads_json_inside_code_fence() -> None:
    label, _ = parse_judgement(
        'Here is my verdict:\n```json\n{"label": "wandering", "explanation": "Repeated queries."}\n```'
    )

    assert label == "wandering"


def test_parse_judgement_falls_back_to_label_substring() -> None:
    label, _ = parse_judgement("The agent is clearly lost here.")

    assert label == "lost"


def test_parse_judgement_raises_on_unrecognizable_response() -> None:
    with pytest.raises(ValueError):
        parse_judgement("no verdict at all")
