"""Golden evaluation dataset helpers (Phoenix)."""

import json
from pathlib import Path
from typing import Any

from phoenix.client import Client
from phoenix.client.resources.datasets import Dataset

DEFAULT_DATASET_NAME = "talkingcode-golden-v1"
DEFAULT_BASE_URL = "https://phoenix.chidinweke.be"
GOLDEN_DATASET_PATH = Path(__file__).with_name("golden_dataset.json")


def get_phoenix_client(*, base_url: str, api_key: str | None = None) -> Client:
    return Client(base_url=base_url, api_key=api_key)


def load_golden_records(path: Path = GOLDEN_DATASET_PATH) -> list[dict[str, Any]]:
    """Load local golden records in Phoenix example shape.

    Expectations are stored as the example's `output` so evaluators receive
    them through their `expected` parameter.
    """
    payload = json.loads(path.read_text())
    return [
        {
            "input": {"question": item["question"]},
            "output": item["expectations"] | {"case_id": item["id"]},
            "metadata": {"id": item["id"], "category": item["category"]},
        }
        for item in payload
    ]


def find_dataset(client: Client, *, name: str) -> Dataset | None:
    """Return an existing dataset by name, if present."""
    try:
        return client.datasets.get_dataset(dataset=name)
    except ValueError as exc:
        if "Dataset not found" in str(exc):
            return None
        raise


def sync_golden_dataset(
    client: Client,
    *,
    dataset_name: str = DEFAULT_DATASET_NAME,
) -> Dataset:
    """Create the golden dataset, or append records not yet present.

    Phoenix datasets are append-only and versioned: records are deduped by
    metadata id, so editing an existing case's expectations requires bumping
    its id (or the dataset name).
    """
    records = load_golden_records()
    dataset = find_dataset(client, name=dataset_name)
    if dataset is None:
        return client.datasets.create_dataset(
            name=dataset_name,
            dataset_description="TalkingCode golden regression set",
            inputs=[record["input"] for record in records],
            outputs=[record["output"] for record in records],
            metadata=[record["metadata"] for record in records],
        )

    existing_ids = {example["metadata"].get("id") for example in dataset.examples}
    new_records = [
        record for record in records if record["metadata"]["id"] not in existing_ids
    ]
    if not new_records:
        return dataset
    return client.datasets.add_examples_to_dataset(
        dataset=dataset_name,
        inputs=[record["input"] for record in new_records],
        outputs=[record["output"] for record in new_records],
        metadata=[record["metadata"] for record in new_records],
    )


def list_evaluation_datasets(client: Client) -> list[dict[str, Any]]:
    """List Phoenix datasets."""
    return [
        {
            "name": dataset["name"],
            "dataset_id": dataset["id"],
            "description": dataset.get("description"),
        }
        for dataset in client.datasets.list()
    ]
