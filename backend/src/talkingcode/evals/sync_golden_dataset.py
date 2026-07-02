"""Sync the local golden dataset into Phoenix."""

import argparse
import os

from talkingcode.evals.dataset import (
    DEFAULT_BASE_URL,
    DEFAULT_DATASET_NAME,
    get_phoenix_client,
    sync_golden_dataset,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", DEFAULT_BASE_URL),
    )
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    client = get_phoenix_client(
        base_url=args.base_url,
        api_key=os.getenv("PHOENIX_API_KEY"),
    )
    dataset = sync_golden_dataset(client, dataset_name=args.dataset_name)
    print(f"Synced dataset {dataset.name} ({dataset.id}).")


if __name__ == "__main__":
    main()
