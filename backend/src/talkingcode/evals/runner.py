"""Run TalkingCode golden evaluations with Phoenix."""

import argparse
import asyncio
import re
import sys
import time
from typing import Any
from uuid import uuid4

from talkingcode.config import AppConfig
from talkingcode.evals.dataset import (
    DEFAULT_BASE_URL,
    DEFAULT_DATASET_NAME,
    find_dataset,
    get_phoenix_client,
    sync_golden_dataset,
)
from talkingcode.evals.scorers import deterministic_evaluators
from talkingcode.factory import AppFactory
from talkingcode.repository.database import get_session
from talkingcode.startup import setup_openai_agents_tracing, setup_telemetry_if_enabled

TOOL_TAG_RE = re.compile(r"<tc-tool\b(?P<attrs>[^>]*)>")
TOOL_NAME_RE = re.compile(r'\bname="(?P<name>[^"]+)"')

DEFAULT_EXPERIMENT_NAME = "talkingcode-golden"


def _extract_tool_names(markdown: str) -> list[str]:
    names = []
    for match in TOOL_TAG_RE.finditer(markdown):
        name_match = TOOL_NAME_RE.search(match.group("attrs"))
        if name_match:
            names.append(name_match.group("name"))
    return names


async def _run_agent(question: str, model_name: str | None) -> dict[str, Any]:
    config = AppConfig.from_env()
    started = time.perf_counter()
    chunks: list[str] = []
    tool_names: list[str] = []

    async with get_session(config.database_url) as session:
        factory = AppFactory(session=session, config=config)
        controller = await factory.get_chat_controller()
        async for event in controller.start_agentic_turn(
            conversation_id=uuid4(),
            question=question,
            selected_model=model_name,
        ):
            if event.event != "markdown.delta":
                continue
            text = str(event.data.get("text", ""))
            chunks.append(text)
            tool_names.extend(_extract_tool_names(text))

    final_answer = "".join(
        chunk for chunk in chunks if not chunk.startswith("<tc-tool")
    )
    latency_ms = int((time.perf_counter() - started) * 1000)
    return {
        "final_answer": final_answer,
        "tool_names": tool_names,
        "tool_call_count": len(tool_names),
        "latency_ms": latency_ms,
    }


def predict(question: str, model_name: str | None = None) -> dict[str, Any]:
    """Synchronous wrapper used as the Phoenix experiment task."""
    return asyncio.run(_run_agent(question, model_name))


def run_golden_evaluation(args: argparse.Namespace) -> Any:
    config = AppConfig.from_env()
    setup_telemetry_if_enabled(config)
    setup_openai_agents_tracing()
    client = get_phoenix_client(
        base_url=args.base_url or config.phoenix_collector_endpoint or DEFAULT_BASE_URL,
        api_key=config.phoenix_api_key,
    )
    dataset = find_dataset(client, name=args.dataset_name)
    if dataset is None or args.sync_dataset:
        dataset = sync_golden_dataset(client, dataset_name=args.dataset_name)

    def task(input: dict[str, Any]) -> dict[str, Any]:
        return predict(input["question"], args.model_name)

    return client.experiments.run_experiment(
        dataset=dataset,
        task=task,
        evaluators=deterministic_evaluators(),
        experiment_name=args.experiment_name,
        dry_run=args.dry_run,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url")
    parser.add_argument(
        "--experiment-name",
        default=DEFAULT_EXPERIMENT_NAME,
    )
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument("--model-name")
    parser.add_argument("--sync-dataset", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    result = run_golden_evaluation(build_parser().parse_args())
    sys.stdout.write(f"{result}\n")


if __name__ == "__main__":
    main()
