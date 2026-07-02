"""Golden evaluation dataset helpers."""

import json
from pathlib import Path
from typing import Any

import mlflow
from mlflow.genai.datasets import create_dataset, search_datasets

DEFAULT_DATASET_NAME = "talkingcode-golden-v1"
DEFAULT_EXPERIMENT_NAME = "talkingcode-agent-dev"
DEFAULT_TRACKING_URI = "http://localhost:5000"
GOLDEN_DATASET_PATH = Path(__file__).with_name("golden_dataset.json")


def configure_mlflow(
    *,
    tracking_uri: str = DEFAULT_TRACKING_URI,
    experiment_name: str = DEFAULT_EXPERIMENT_NAME,
) -> str:
    """Configure MLflow and return the experiment id."""
    mlflow.set_tracking_uri(tracking_uri)
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(experiment_name)
    else:
        experiment_id = experiment.experiment_id
    mlflow.set_experiment(experiment_name=experiment_name)
    return experiment_id


def load_golden_records(path: Path = GOLDEN_DATASET_PATH) -> list[dict[str, Any]]:
    """Load local golden records in MLflow GenAI dataset shape."""
    payload = json.loads(path.read_text())
    records = []
    for item in payload:
        records.append(
            {
                "inputs": {"question": item["question"]},
                "expectations": item["expectations"] | {"case_id": item["id"]},
                "tags": {"id": item["id"], "category": item["category"]},
            }
        )
    return records


def find_dataset(*, name: str, experiment_id: str):
    """Return an existing dataset by name for the experiment, if present."""
    datasets = search_datasets(experiment_ids=[experiment_id])
    return next((dataset for dataset in datasets if dataset.name == name), None)


def sync_golden_dataset(
    *,
    dataset_name: str = DEFAULT_DATASET_NAME,
    tracking_uri: str = DEFAULT_TRACKING_URI,
    experiment_name: str = DEFAULT_EXPERIMENT_NAME,
):
    """Create or update the MLflow golden dataset from the local JSON file."""
    experiment_id = configure_mlflow(
        tracking_uri=tracking_uri,
        experiment_name=experiment_name,
    )
    dataset = find_dataset(name=dataset_name, experiment_id=experiment_id)
    if dataset is None:
        dataset = create_dataset(
            name=dataset_name,
            experiment_id=[experiment_id],
            tags={"source": "backend/src/talkingcode/evals/golden_dataset.json"},
        )

    dataset.merge_records(load_golden_records())
    return dataset


def list_evaluation_datasets(
    *,
    tracking_uri: str = DEFAULT_TRACKING_URI,
    experiment_name: str = DEFAULT_EXPERIMENT_NAME,
) -> list[dict[str, Any]]:
    """List MLflow GenAI datasets for the configured experiment."""
    experiment_id = configure_mlflow(
        tracking_uri=tracking_uri,
        experiment_name=experiment_name,
    )
    datasets = search_datasets(experiment_ids=[experiment_id])
    result = []
    for dataset in datasets:
        frame = dataset.to_df()
        result.append(
            {
                "name": dataset.name,
                "dataset_id": dataset.dataset_id,
                "digest": dataset.digest,
                "record_count": len(frame),
                "experiment_ids": list(dataset.experiment_ids),
            }
        )
    return result

