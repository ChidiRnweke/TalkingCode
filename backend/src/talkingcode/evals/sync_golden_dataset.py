"""Sync the local golden dataset into MLflow."""

import argparse
import os

from talkingcode.evals.dataset import (
    DEFAULT_DATASET_NAME,
    DEFAULT_EXPERIMENT_NAME,
    DEFAULT_TRACKING_URI,
    sync_golden_dataset,
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
    return parser


def main() -> None:
    args = build_parser().parse_args()
    dataset = sync_golden_dataset(
        dataset_name=args.dataset_name,
        tracking_uri=args.tracking_uri,
        experiment_name=args.experiment_name,
    )
    print(f"Synced dataset {dataset.name} ({dataset.dataset_id}).")


if __name__ == "__main__":
    main()

