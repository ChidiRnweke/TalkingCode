from dataclasses import dataclass
from typing import Any

from opentelemetry.metrics import get_meter

meter = get_meter("talkingcode.ingestion")


@dataclass(frozen=True, slots=True)
class IngestionMetrics:
    ingestion_runs_total: Any
    ingestion_files_total: Any
    ingestion_files_failed_total: Any
    ingestion_classifier_fallback_total: Any
    ingestion_embedding_requests_total: Any
    ingestion_github_requests_total: Any
    ingestion_chunks_total: Any
    ingestion_embeddings_total: Any
    ingestion_run_duration_seconds: Any
    ingestion_file_duration_seconds: Any
    ingestion_github_request_duration_seconds: Any
    ingestion_embedding_request_duration_seconds: Any
    ingestion_chunking_duration_seconds: Any
    ingestion_classification_duration_seconds: Any
    ingestion_db_write_duration_seconds: Any
    ingestion_file_size_bytes: Any
    ingestion_chunk_count_per_file: Any


_metrics: IngestionMetrics | None = None


def get_ingestion_metrics() -> IngestionMetrics:
    global _metrics
    if _metrics is not None:
        return _metrics

    _metrics = IngestionMetrics(
        ingestion_runs_total=meter.create_counter("ingestion_runs_total"),
        ingestion_files_total=meter.create_counter("ingestion_files_total"),
        ingestion_files_failed_total=meter.create_counter(
            "ingestion_files_failed_total"
        ),
        ingestion_classifier_fallback_total=meter.create_counter(
            "ingestion_classifier_fallback_total"
        ),
        ingestion_embedding_requests_total=meter.create_counter(
            "ingestion_embedding_requests_total"
        ),
        ingestion_github_requests_total=meter.create_counter(
            "ingestion_github_requests_total"
        ),
        ingestion_chunks_total=meter.create_counter("ingestion_chunks_total"),
        ingestion_embeddings_total=meter.create_counter("ingestion_embeddings_total"),
        ingestion_run_duration_seconds=meter.create_histogram(
            "ingestion_run_duration_seconds", unit="s"
        ),
        ingestion_file_duration_seconds=meter.create_histogram(
            "ingestion_file_duration_seconds", unit="s"
        ),
        ingestion_github_request_duration_seconds=meter.create_histogram(
            "ingestion_github_request_duration_seconds", unit="s"
        ),
        ingestion_embedding_request_duration_seconds=meter.create_histogram(
            "ingestion_embedding_request_duration_seconds", unit="s"
        ),
        ingestion_chunking_duration_seconds=meter.create_histogram(
            "ingestion_chunking_duration_seconds", unit="s"
        ),
        ingestion_classification_duration_seconds=meter.create_histogram(
            "ingestion_classification_duration_seconds", unit="s"
        ),
        ingestion_db_write_duration_seconds=meter.create_histogram(
            "ingestion_db_write_duration_seconds", unit="s"
        ),
        ingestion_file_size_bytes=meter.create_histogram(
            "ingestion_file_size_bytes", unit="By"
        ),
        ingestion_chunk_count_per_file=meter.create_histogram(
            "ingestion_chunk_count_per_file"
        ),
    )
    return _metrics
