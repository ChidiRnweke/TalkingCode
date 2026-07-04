"""Golden evaluation dataset helpers (Phoenix)."""

import json
from pathlib import Path
from typing import Any

from phoenix.client import AsyncClient
from phoenix.client.resources.datasets import Dataset

DEFAULT_DATASET_NAME = "talkingcode-golden-v1"
DEFAULT_BASE_URL = "https://phoenix.chidinweke.be"
GOLDEN_DATASET_PATH = Path(__file__).with_name("golden_dataset.json")


def get_phoenix_client(*, base_url: str, api_key: str | None = None) -> AsyncClient:
    return AsyncClient(base_url=base_url, api_key=api_key or None)


def load_golden_records(path: Path = GOLDEN_DATASET_PATH) -> list[dict[str, Any]]:
    """Load local golden records in Phoenix example shape.

    Expectations are stored as the example's `output` so evaluators receive
    them through their `expected` parameter. The case id doubles as the
    example's stable id (diff-sync key) and the category as its split.
    """
    payload = json.loads(path.read_text())
    return [
        {
            "id": item["id"],
            "input": {"question": item["question"]},
            "output": item["expectations"] | {"case_id": item["id"]},
            "metadata": {"id": item["id"], "category": item["category"]},
            "splits": [item["category"]],
        }
        for item in payload
    ]


async def find_dataset(client: AsyncClient, *, name: str) -> Dataset | None:
    """Return an existing dataset by name, if present."""
    try:
        return await client.datasets.get_dataset(dataset=name)
    except ValueError as exc:
        if "Dataset not found" in str(exc):
            return None
        raise


async def sync_golden_dataset(
    client: AsyncClient,
    *,
    dataset_name: str = DEFAULT_DATASET_NAME,
) -> Dataset:
    """Diff-sync the local golden records into Phoenix.

    Examples carry stable ids, so Phoenix applies the minimal set of adds,
    edits, and deletes against the current dataset version; editing a case
    locally and re-syncing updates it in place.
    """
    return await client.datasets.create_dataset(
        name=dataset_name,
        dataset_description="TalkingCode golden regression set",
        examples=load_golden_records(),
    )


async def list_evaluation_datasets(client: AsyncClient) -> list[dict[str, Any]]:
    """List Phoenix datasets."""
    return [
        {
            "name": dataset["name"],
            "dataset_id": dataset["id"],
            "description": dataset.get("description"),
        }
        for dataset in await client.datasets.list()
    ]
