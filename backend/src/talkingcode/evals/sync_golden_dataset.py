"""Sync the local golden dataset into Phoenix."""

import argparse
import sys

from talkingcode.config import AppConfig
from talkingcode.evals.dataset import (
    DEFAULT_BASE_URL,
    DEFAULT_DATASET_NAME,
    get_phoenix_client,
    sync_golden_dataset,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url")
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET_NAME)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = AppConfig.from_env()
    client = get_phoenix_client(
        base_url=args.base_url or config.phoenix_base_url or DEFAULT_BASE_URL,
        api_key=config.phoenix_api_key,
    )
    dataset = sync_golden_dataset(client, dataset_name=args.dataset_name)
    sys.stdout.write(f"Synced dataset {dataset.name} ({dataset.id}).\n")


if __name__ == "__main__":
    main()
