"""List MLflow GenAI datasets for TalkingCode."""

import argparse
import json
import os

from talkingcode.evals.dataset import (
    DEFAULT_EXPERIMENT_NAME,
    DEFAULT_TRACKING_URI,
    list_evaluation_datasets,
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
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    datasets = list_evaluation_datasets(
        tracking_uri=args.tracking_uri,
        experiment_name=args.experiment_name,
    )
    if args.json:
        print(json.dumps(datasets, indent=2))
        return

    if not datasets:
        print("No evaluation datasets found.")
        return

    for dataset in datasets:
        print(
            f"{dataset['name']} records={dataset['record_count']} "
            f"id={dataset['dataset_id']} digest={dataset['digest']}"
        )


if __name__ == "__main__":
    main()

