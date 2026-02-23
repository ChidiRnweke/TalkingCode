from dataclasses import dataclass
from opentelemetry.metrics import get_meter

meter = get_meter("talkingcode.ingestion")


@dataclass(frozen=True, slots=True)
class IngestionMetrics:
    ingestion_runs_total: any
    ingestion_files_total: any
    ingestion_files_failed_total: any
    ingestion_classifier_fallback_total: any
    ingestion_embedding_requests_total: any
    ingestion_github_requests_total: any
    ingestion_chunks_total: any
    ingestion_embeddings_total: any
    ingestion_run_duration_seconds: any
    ingestion_file_duration_seconds: any
    ingestion_github_request_duration_seconds: any
    ingestion_embedding_request_duration_seconds: any
    ingestion_chunking_duration_seconds: any
    ingestion_classification_duration_seconds: any
    ingestion_db_write_duration_seconds: any
    ingestion_file_size_bytes: any
    ingestion_chunk_count_per_file: any


_metrics: IngestionMetrics | None = None


def get_ingestion_metrics() -> IngestionMetrics:
    global _metrics
    if _metrics is not None:
        return _metrics

    _metrics = IngestionMetrics(
        ingestion_runs_total=meter.create_counter("ingestion_runs_total"),
        ingestion_files_total=meter.create_counter("ingestion_files_total"),
        ingestion_files_failed_total=meter.create_counter("ingestion_files_failed_total"),
        ingestion_classifier_fallback_total=meter.create_counter("ingestion_classifier_fallback_total"),
        ingestion_embedding_requests_total=meter.create_counter("ingestion_embedding_requests_total"),
        ingestion_github_requests_total=meter.create_counter("ingestion_github_requests_total"),
        ingestion_chunks_total=meter.create_counter("ingestion_chunks_total"),
        ingestion_embeddings_total=meter.create_counter("ingestion_embeddings_total"),
        ingestion_run_duration_seconds=meter.create_histogram("ingestion_run_duration_seconds", unit="s"),
        ingestion_file_duration_seconds=meter.create_histogram("ingestion_file_duration_seconds", unit="s"),
        ingestion_github_request_duration_seconds=meter.create_histogram("ingestion_github_request_duration_seconds", unit="s"),
        ingestion_embedding_request_duration_seconds=meter.create_histogram("ingestion_embedding_request_duration_seconds", unit="s"),
        ingestion_chunking_duration_seconds=meter.create_histogram("ingestion_chunking_duration_seconds", unit="s"),
        ingestion_classification_duration_seconds=meter.create_histogram("ingestion_classification_duration_seconds", unit="s"),
        ingestion_db_write_duration_seconds=meter.create_histogram("ingestion_db_write_duration_seconds", unit="s"),
        ingestion_file_size_bytes=meter.create_histogram("ingestion_file_size_bytes", unit="By"),
        ingestion_chunk_count_per_file=meter.create_histogram("ingestion_chunk_count_per_file"),
    )
    return _metrics
