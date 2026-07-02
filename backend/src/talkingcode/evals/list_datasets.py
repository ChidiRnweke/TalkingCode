"""List Phoenix datasets for TalkingCode."""

import argparse
import json
import os

from talkingcode.evals.dataset import (
    DEFAULT_BASE_URL,
    get_phoenix_client,
    list_evaluation_datasets,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.getenv("PHOENIX_COLLECTOR_ENDPOINT", DEFAULT_BASE_URL),
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    client = get_phoenix_client(
        base_url=args.base_url,
        api_key=os.getenv("PHOENIX_API_KEY"),
    )
    datasets = list_evaluation_datasets(client)
    if args.json:
        print(json.dumps(datasets, indent=2))
        return

    if not datasets:
        print("No evaluation datasets found.")
        return

    for dataset in datasets:
        print(f"{dataset['name']} id={dataset['dataset_id']}")


if __name__ == "__main__":
    main()
