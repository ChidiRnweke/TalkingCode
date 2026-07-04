"""List Phoenix datasets for TalkingCode."""

import argparse
import json
import sys

from talkingcode.config import AppConfig
from talkingcode.evals.dataset import (
    DEFAULT_BASE_URL,
    get_phoenix_client,
    list_evaluation_datasets,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = AppConfig.from_env()
    client = get_phoenix_client(
        base_url=args.base_url or config.phoenix_collector_endpoint or DEFAULT_BASE_URL,
        api_key=config.phoenix_api_key,
    )
    datasets = list_evaluation_datasets(client)
    if args.json:
        sys.stdout.write(f"{json.dumps(datasets, indent=2)}\n")
        return

    if not datasets:
        sys.stdout.write("No evaluation datasets found.\n")
        return

    for dataset in datasets:
        sys.stdout.write(f"{dataset['name']} id={dataset['dataset_id']}\n")


if __name__ == "__main__":
    main()
