"""Run TalkingCode golden evaluations with MLflow."""

import argparse
import asyncio
import os
import re
import time
from typing import Any
from uuid import uuid4

import mlflow

from talkingcode.config import AppConfig
from talkingcode.evals.dataset import (
    DEFAULT_DATASET_NAME,
    DEFAULT_EXPERIMENT_NAME,
    DEFAULT_TRACKING_URI,
    configure_mlflow,
    find_dataset,
    load_golden_records,
    sync_golden_dataset,
)
from talkingcode.evals.scorers import deterministic_scorers
from talkingcode.factory import AppFactory
from talkingcode.repository.database import get_session
from talkingcode.startup import configure_mlflow_tracing

TOOL_TAG_RE = re.compile(r"<tc-tool\b(?P<attrs>[^>]*)>")
TOOL_NAME_RE = re.compile(r'\bname="(?P<name>[^"]+)"')


def _extract_tool_names(markdown: str) -> list[str]:
    names = []
    for match in TOOL_TAG_RE.finditer(markdown):
        name_match = TOOL_NAME_RE.search(match.group("attrs"))
        if name_match:
            names.append(name_match.group("name"))
    return names


async def _run_agent(question: str, model_name: str | None) -> dict[str, Any]:
    config = AppConfig.from_env()
    configure_mlflow_tracing(config)
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
    """Synchronous wrapper used by MLflow evaluate."""
    return asyncio.run(_run_agent(question, model_name))


async def _build_eval_rows(model_name: str | None) -> list[dict[str, Any]]:
    rows = []
    for record in load_golden_records():
        question = record["inputs"]["question"]
        try:
            outputs = await _run_agent(question, model_name)
        except Exception as exc:  # noqa: BLE001
            outputs = {
                "final_answer": "",
                "tool_names": [],
                "tool_call_count": 0,
                "latency_ms": None,
                "error": f"{type(exc).__name__}: {exc}",
            }
        rows.append(record | {"outputs": outputs})
    return rows


def run_golden_evaluation(args: argparse.Namespace) -> Any:
    experiment_id = configure_mlflow(
        tracking_uri=args.tracking_uri,
        experiment_name=args.experiment_name,
    )
    dataset = find_dataset(name=args.dataset_name, experiment_id=experiment_id)
    if dataset is None or args.sync_dataset:
        dataset = sync_golden_dataset(
            dataset_name=args.dataset_name,
            tracking_uri=args.tracking_uri,
            experiment_name=args.experiment_name,
        )

    rows = asyncio.run(_build_eval_rows(args.model_name))
    return mlflow.genai.evaluate(
        data=rows,
        scorers=deterministic_scorers(),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tracking-uri",
        default=os.getenv("MLFLOW_TRACKING_URI", DEFAULT_TRACKING_URI),
    )
    parser.add_argument(
        "--experiment-name",
        default=os.getenv("MLFLOW_EXPERIMENT_NAME", DEFAULT_EXPERIMENT_NAME),
    )
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    parser.add_argument("--model-name", default=os.getenv("EVAL_MODEL_NAME"))
    parser.add_argument("--sync-dataset", action="store_true")
    return parser


def main() -> None:
    result = run_golden_evaluation(build_parser().parse_args())
    print(result)


if __name__ == "__main__":
    main()
