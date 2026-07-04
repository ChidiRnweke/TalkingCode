"""Run TalkingCode golden evaluations with Phoenix."""

import argparse
import asyncio
import sys
from typing import Any

from talkingcode.config import AppConfig
from talkingcode.evals.dataset import (
    DEFAULT_BASE_URL,
    DEFAULT_DATASET_NAME,
    find_dataset,
    get_phoenix_client,
    sync_golden_dataset,
)
from talkingcode.evals.judge import make_trajectory_judge
from talkingcode.evals.scorers import deterministic_evaluators
from talkingcode.evals.trajectory import run_agent_turn
from talkingcode.factory import AppFactory
from talkingcode.repository.database import get_session
from talkingcode.startup import setup_phoenix_tracing, setup_telemetry_if_enabled

DEFAULT_EXPERIMENT_NAME = "talkingcode-golden"
DEFAULT_TASK_TIMEOUT_S = 180


async def _run_agent(question: str, model_name: str | None) -> dict[str, Any]:
    config = AppConfig.from_env()
    async with get_session(config.database_url) as session:
        factory = AppFactory(session=session, config=config)
        agent_service = await factory.get_chat_agent_service()
        return await run_agent_turn(
            agent_service,
            question=question,
            model_name=model_name or config.default_model,
        )


async def run_golden_evaluation(args: argparse.Namespace) -> Any:
    config = AppConfig.from_env()
    setup_telemetry_if_enabled(config)
    setup_phoenix_tracing(config)
    client = get_phoenix_client(
        base_url=args.base_url or config.phoenix_base_url or DEFAULT_BASE_URL,
        api_key=config.phoenix_api_key,
    )
    dataset = await find_dataset(client, name=args.dataset_name)
    if dataset is None or args.sync_dataset:
        dataset = await sync_golden_dataset(client, dataset_name=args.dataset_name)

    async def task(input: dict[str, Any]) -> dict[str, Any]:
        return await _run_agent(input["question"], args.model_name)

    evaluators: dict[str, Any] = deterministic_evaluators()
    if not args.no_judge:
        evaluators["trajectory_judge"] = make_trajectory_judge(
            api_key=config.openrouter_api_key,
            model=args.judge_model or config.intent_extraction_model,
        )

    return await client.experiments.run_experiment(
        dataset=dataset,
        task=task,
        evaluators=evaluators,
        experiment_name=args.experiment_name,
        dry_run=args.dry_run,
        concurrency=args.concurrency,
        repetitions=args.repetitions,
        timeout=args.timeout,
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
    parser.add_argument("--judge-model")
    parser.add_argument("--no-judge", action="store_true")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TASK_TIMEOUT_S)
    parser.add_argument("--sync-dataset", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    result = asyncio.run(run_golden_evaluation(build_parser().parse_args()))
    sys.stdout.write(f"{result}\n")


if __name__ == "__main__":
    main()
