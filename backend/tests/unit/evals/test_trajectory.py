from talkingcode.evals.trajectory import (
    _output_paths,
    _search_query,
    _summarize_tool_output,
)


def test_summarize_search_output_keeps_paths_and_drops_content() -> None:
    output = {
        "refined_query": "svelte frontend",
        "items": [
            {
                "repository": "chidi/talkingcode",
                "path": "frontend/App.svelte",
                "content": "x" * 700,
            },
        ],
    }

    summary = _summarize_tool_output("search_github", output)

    assert summary == {
        "refined_query": "svelte frontend",
        "paths": ["chidi/talkingcode: frontend/App.svelte"],
    }


def test_summarize_error_output_is_flagged() -> None:
    summary = _summarize_tool_output("read_file", {"error": "File not found"})

    assert summary == {"error": "File not found"}


def test_output_paths_extracts_search_result_paths() -> None:
    output = {"items": [{"path": "a.py"}, {"path": "b.py"}, {"no_path": True}]}

    assert _output_paths("search_github", output) == ["a.py", "b.py"]


def test_output_paths_includes_successfully_read_files_only() -> None:
    read = {"repository": "o/r", "file_path": "src/main.py", "content": "..."}

    assert _output_paths("read_file", read) == ["src/main.py"]
    assert _output_paths("read_file", {"error": "not indexed"}) == []


def test_search_query_parses_arguments_json() -> None:
    call = {"name": "search_github", "arguments": '{"query": "chat runtime"}'}

    assert _search_query(call) == "chat runtime"


def test_search_query_ignores_other_tools_and_bad_json() -> None:
    assert _search_query({"name": "read_file", "arguments": "{}"}) is None
    assert _search_query({"name": "search_github", "arguments": "not json"}) is None
