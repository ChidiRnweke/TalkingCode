# Blueprint: Deployment Hardening with Infisical + OTEL + Ingestion Telemetry

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. **Read this file first.** Every loop, re-read this file before doing anything.
2. **Do the next unchecked step.** Find the first `- [ ]` item. Do that. Only that.
3. **Verify before checking off.** Run the verification commands listed in the step.
4. **Commit after each step.** `git add -A && git commit -m "blueprint: <step title>"`
5. **Do not skip ahead.** Steps are ordered by dependency.
6. **Follow patterns exactly.** Reuse structure from snippets in this plan.
7. **If blocked, document and move on.** Add a note under the blocked step.
8. **Keep this file updated.** If implementation differs, add notes in the step.

---

## Context

This repository already has a working ingestion pipeline and app structure, but deployment concerns are incomplete:

- Secrets are currently environment-only (`backend/src/talkingcode/config.py`).
- Frontend has no production OTEL bootstrap script pattern.
- Backend uses `structlog.getLogger(...)` across modules but has no centralized telemetry bootstrap.
- Ingestion is the most important workload and needs production-grade logging and metrics.
- Docker/compose setup is not production-ready (`docker-compose.yml` is mostly a skeleton with commented services).

The target is to deliver a deployment package with:

1. Infisical-backed secret loading (with env fallback) in backend and frontend server runtime.
2. OTEL bootstrap in frontend using the same pattern as `ReceiptToRecipe/scripts/otel-instrumentation.js`.
3. Backend OTEL + rich ingestion instrumentation (logs + metrics + traces).
4. Python provisioning/migration jobs (ReceiptToRecipe pattern, Python implementation).
5. Production and development compose files with setup profile and observability wiring.

---

## Scope

**In scope:**

- Backend secrets module (`Env` + `Infisical` + `SecretsReader`).
- Frontend secrets loader script for server runtime.
- Frontend OTEL script modeled after ReceiptToRecipe.
- Backend telemetry module and ingestion-focused metrics/logging instrumentation.
- Python setup scripts for provisioning + migrations.
- `docker-compose.prod.yml` and `docker-compose.dev.yml`.
- Dockerfile upgrades for production.
- Documentation updates.

**Out of scope:**

- Business feature refactors.
- Frontend SvelteKit experimental observability flags/instrumentation APIs.
- CI/CD workflow authoring.

---

## Architecture Decisions (Do Not Deviate)

1. **Frontend observability path**: Use Node OTEL bootstrap script (`scripts/otel-instrumentation.js`) and launcher script. Do **not** use SvelteKit experimental observability APIs.
2. **Secrets strategy**: Use a reader abstraction with two backends:
   - env vars (default)
   - Infisical (when `INFISICAL_ENABLED` is set)
3. **Ingestion telemetry strategy**:
   - logs: high-cardinality context is allowed (`path`, `run_id`)
   - metrics: bounded-cardinality attributes only (no file path)
   - traces: run-level and stage-level spans
4. **Deployment lifecycle**:
   - setup profile service(s) handle provision + migration
   - app service starts without schema creation side effects

---

## Existing Patterns You Must Copy

### A) Infisical/env reader pattern (Python)

Source pattern: your shared env file.

Use these exact design elements:

- `SecretsBackend` `Protocol`
- `EnvSecretsBackend` dataclass
- `InfisicalSecretsBackend` dataclass with `from_env`
- `SecretsReader.from_env()` chooses backend by `INFISICAL_ENABLED`
- helper functions:
  - `get_env_or_raise`
  - `env_var_or_default`

### B) OTEL bootstrap pattern (Node)

Source pattern: ReceiptToRecipe `scripts/otel-instrumentation.js`.

Use these exact design elements:

- `NodeSDK` + auto instrumentations
- OTLP trace exporter + OTLP logs exporter
- global single-init guard
- console bridge to OTEL logs
- safe no-op when endpoint not configured

### C) Backend telemetry module layout

Source pattern: your shared telemetry package.

Use these files and rough responsibilities:

- `configure.py`: initialize logs/metrics/spans exporters
- `helpers.py`: metadata helpers
- `logging.py`: error decorators/helpers
- `metrics.py`: timing decorators/helpers
- `__init__.py`: explicit exports

### D) Ingestion service shape

Use existing files exactly (no broad refactor):

- `backend/src/talkingcode/services/ingestion/ingestion_service.py`
- `backend/src/talkingcode/services/ingestion/github_fetcher.py`
- `backend/src/talkingcode/services/ingestion/embedder.py`
- `backend/src/talkingcode/services/classification/document_classifier.py`

---

## Interfaces and Contracts

### Backend env vars contract

Required for normal backend runtime:

- `DATABASE_URL`
- `OPENROUTER_API_KEY`
- `INGESTION_API_KEY`

Optional but recommended:

- `GITHUB_TOKEN`
- `OTEL_EXPORTER_OTLP_ENDPOINT`
- `OTEL_SERVICE_NAME`
- `OTEL_ENVIRONMENT`

Infisical mode required vars:

- `INFISICAL_ENABLED=1`
- `INFISICAL_CLIENT_ID`
- `INFISICAL_CLIENT_SECRET`
- `INFISICAL_PROJECT_ID`
- `INFISICAL_ENVIRONMENT`
- `INFISICAL_URL`

### Frontend server runtime env contract

Required:

- `BACKEND_URL`

Optional:

- `PUBLIC_BACKEND_URL`
- `INGESTION_API_KEY`
- all OTEL vars
- all Infisical vars (if frontend will source runtime secrets)

---

## Plan

- [x] **Step 1: Implement backend secrets reader module and wire AppConfig**

  **Files to create/modify**

  - Create: `backend/src/talkingcode/environment/env.py`
  - Create: `backend/src/talkingcode/environment/__init__.py`
  - Modify: `backend/src/talkingcode/config.py`
  - Modify: `backend/alembic/env.py`
  - Modify: `backend/pyproject.toml`

  **Exact code pattern to copy (use as baseline, adapt imports only):**

  ```python
  # backend/src/talkingcode/environment/env.py
  import os
  from dataclasses import dataclass
  from typing import Protocol, Self

  from dotenv import load_dotenv
  from infisical_client import (
      AuthenticationOptions,
      ClientSettings,
      GetSecretOptions,
      InfisicalClient,
      UniversalAuthMethod,
  )
  import structlog

  logger = structlog.getLogger("talkingcode")


  class SecretsNotFoundError(Exception):
      pass


  class SecretsBackend(Protocol):
      def read_secret(self, secret_name: str) -> str: ...
      def read_or_default(self, secret_name: str, default: str) -> str: ...
      def read_optional(self, secret_name: str) -> str | None: ...


  @dataclass(frozen=True, slots=True)
  class EnvSecretsBackend(SecretsBackend):
      def read_secret(self, secret_name: str) -> str:
          return get_env_or_raise(secret_name)

      def read_or_default(self, secret_name: str, default: str) -> str:
          return env_var_or_default(secret_name, default)

      def read_optional(self, secret_name: str) -> str | None:
          return os.getenv(secret_name)


  @dataclass(frozen=True, slots=True)
  class InfisicalSecretsBackend(SecretsBackend):
      client: InfisicalClient
      project_id: str
      environment: str

      def read_secret(self, secret_name: str) -> str:
          try:
              secret = self.client.getSecret(
                  options=GetSecretOptions(
                      environment=self.environment,
                      project_id=self.project_id,
                      secret_name=secret_name,
                  )
              )
              return secret.secret_value
          except Exception as exc:  # noqa: BLE001
              raise SecretsNotFoundError(f"Secret {secret_name} not found") from exc

      def read_or_default(self, secret_name: str, default: str) -> str:
          return self.read_optional(secret_name) or default

      def read_optional(self, secret_name: str) -> str | None:
          try:
              return self.read_secret(secret_name)
          except Exception:
              return None

      @classmethod
      def from_env(cls) -> Self:
          client_id = get_env_or_raise("INFISICAL_CLIENT_ID")
          client_secret = get_env_or_raise("INFISICAL_CLIENT_SECRET")
          project_id = get_env_or_raise("INFISICAL_PROJECT_ID")
          environment = get_env_or_raise("INFISICAL_ENVIRONMENT")
          url = get_env_or_raise("INFISICAL_URL")

          auth = UniversalAuthMethod(client_id=client_id, client_secret=client_secret)
          auth_options = AuthenticationOptions(universal_auth=auth)
          client_settings = ClientSettings(auth=auth_options, site_url=url)
          client = InfisicalClient(client_settings)
          return cls(client=client, project_id=project_id, environment=environment)


  @dataclass(frozen=True, slots=True)
  class SecretsReader:
      backend: SecretsBackend

      def read_secret(self, secret_name: str) -> str:
          return self.backend.read_secret(secret_name)

      def read_or_default(self, secret_name: str, default: str) -> str:
          return self.backend.read_or_default(secret_name, default)

      def read_optional(self, secret_name: str) -> str | None:
          return self.backend.read_optional(secret_name)

      @classmethod
      def from_env(cls) -> Self:
          load_dotenv()
          enabled = os.getenv("INFISICAL_ENABLED")
          if enabled:
              logger.info("secrets.backend.infisical.enabled")
              return cls(backend=InfisicalSecretsBackend.from_env())
          logger.info("secrets.backend.env.enabled")
          return cls(backend=EnvSecretsBackend())


  def env_var_or_default(var_name: str, default: str) -> str:
      value = os.getenv(var_name)
      if value is None:
          logger.warning("env.default.used", var=var_name)
          return default
      return value


  def get_env_or_raise(var_name: str) -> str:
      value = os.getenv(var_name)
      if value is None:
          logger.error("env.required.missing", var=var_name)
          raise SecretsNotFoundError(f"Missing env var: {var_name}")
      return value
  ```

  **AppConfig wiring snippet (replace direct BaseSettings access):**

  ```python
  # inside AppConfig.from_env()
  reader = SecretsReader.from_env()
  return cls(
      database_url=reader.read_secret("DATABASE_URL"),
      openrouter_api_key=reader.read_secret("OPENROUTER_API_KEY"),
      github_token=reader.read_or_default("GITHUB_TOKEN", ""),
      ingestion_api_key=reader.read_secret("INGESTION_API_KEY"),
      environment=reader.read_or_default("ENVIRONMENT", "development"),
      log_level=reader.read_or_default("LOG_LEVEL", "INFO"),
      default_model=reader.read_or_default("DEFAULT_MODEL", "anthropic/claude-3.5-sonnet"),
      fallback_model=reader.read_or_default("FALLBACK_MODEL", "google/gemini-3-flash"),
      max_iterations=int(reader.read_or_default("MAX_ITERATIONS", "8")),
      max_tools_per_turn=int(reader.read_or_default("MAX_TOOLS_PER_TURN", "3")),
      default_tool_timeout=int(reader.read_or_default("DEFAULT_TOOL_TIMEOUT", "15")),
      embedding_model=reader.read_or_default("EMBEDDING_MODEL", "openai/text-embedding-3-large"),
      embedding_dimensions=int(reader.read_or_default("EMBEDDING_DIMENSIONS", "3072")),
      intent_extraction_model=reader.read_or_default("INTENT_EXTRACTION_MODEL", "deepseek/deepseek-v3.2"),
      curated_models=reader.read_or_default("CURATED_MODELS", ""),
      default_chat_model=reader.read_or_default("DEFAULT_CHAT_MODEL", "google/gemini-3-flash-preview"),
  )
  ```

  **Verification commands**

  ```bash
  uv --directory backend run python -c "from talkingcode.config import AppConfig; print(AppConfig.from_env().environment)"
  uv --directory backend run alembic current
  ```

  **Done criteria**

  - `AppConfig.from_env()` reads via `SecretsReader`.
  - Alembic resolves DB URL through same path.

- [x] **Step 2: Add backend telemetry core module and initialize it at startup**

  **Files to create/modify**

  - Create: `backend/src/talkingcode/telemetry/{__init__.py,configure.py,helpers.py,logging.py,metrics.py}`
  - Modify: `backend/src/talkingcode/app.py`
  - Modify: `backend/src/talkingcode/dependencies.py`
  - Modify: `backend/pyproject.toml`

  **Reference snippet for configure.py (adapt service name/env):**

  ```python
  import logging
  import structlog

  from opentelemetry._logs import set_logger_provider
  from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
  from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
  from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
  from opentelemetry.metrics import set_meter_provider
  from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
  from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
  from opentelemetry.sdk.metrics import MeterProvider
  from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
  from opentelemetry.sdk.resources import Resource
  from opentelemetry.sdk.trace import TracerProvider
  from opentelemetry.sdk.trace.export import BatchSpanProcessor
  from opentelemetry.trace import get_current_span, set_tracer_provider


  def configure_telemetry(endpoint: str, service_name: str, environment: str) -> None:
      resource = Resource.create(
          {
              "service.name": service_name,
              "deployment.environment": environment,
          }
      )

      _configure_spans(endpoint, resource)
      _configure_metrics(endpoint, resource)
      _configure_logs(endpoint, resource)


  def _configure_spans(endpoint: str, resource: Resource) -> None:
      span_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
      tracer_provider = TracerProvider(resource=resource)
      tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
      set_tracer_provider(tracer_provider)


  def _configure_metrics(endpoint: str, resource: Resource) -> None:
      metric_exporter = OTLPMetricExporter(endpoint=endpoint, insecure=True)
      metric_reader = PeriodicExportingMetricReader(metric_exporter)
      meter_provider = MeterProvider([metric_reader], resource)
      set_meter_provider(meter_provider)


  def _configure_logs(endpoint: str, resource: Resource) -> None:
      log_exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)
      logger_provider = LoggerProvider(resource=resource)
      logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
      set_logger_provider(logger_provider)

      handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
      logging.getLogger("talkingcode").addHandler(handler)
      logging.getLogger("talkingcode").setLevel(logging.INFO)

      structlog.configure(
          processors=[
              structlog.stdlib.filter_by_level,
              structlog.processors.TimeStamper(fmt="iso"),
              _add_span_context,
              structlog.processors.JSONRenderer(),
          ],
          logger_factory=structlog.stdlib.LoggerFactory(),
          wrapper_class=structlog.stdlib.BoundLogger,
          cache_logger_on_first_use=True,
      )


  def _add_span_context(_, __, event_dict):
      span = get_current_span()
      if not span.is_recording():
          return event_dict
      ctx = span.get_span_context()
      event_dict["trace_id"] = hex(ctx.trace_id)
      event_dict["span_id"] = hex(ctx.span_id)
      return event_dict
  ```

  **Startup wiring snippet in `app.py` lifespan:**

  ```python
  # near startup in lifespan()
  config = AppConfig.from_env()
  endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
  service_name = os.getenv("OTEL_SERVICE_NAME", "talkingcode-backend")
  otel_env = os.getenv("OTEL_ENVIRONMENT", config.environment)
  if endpoint:
      configure_telemetry(endpoint=endpoint, service_name=service_name, environment=otel_env)
      logger.info("telemetry.enabled", endpoint=endpoint, service_name=service_name)
  else:
      logger.info("telemetry.disabled")
  ```

  **Important cleanup**

  - Remove `print(...)` lines in `backend/src/talkingcode/dependencies.py`.

  **Verification commands**

  ```bash
  uv --directory backend run python -c "from talkingcode.app import create_app; app=create_app(); print(app.title)"
  ```

  **Done criteria**

  - Telemetry initialization is centralized.
  - No debug prints remain in dependencies.

- [ ] **Step 3: Add dedicated ingestion metrics registry**

  **Files to create**

  - Create: `backend/src/talkingcode/telemetry/ingestion_metrics.py`

  **Exact metrics to define (names fixed):**

  - Counters
    - `ingestion_runs_total`
    - `ingestion_files_total`
    - `ingestion_files_failed_total`
    - `ingestion_classifier_fallback_total`
    - `ingestion_embedding_requests_total`
    - `ingestion_github_requests_total`
    - `ingestion_chunks_total`
    - `ingestion_embeddings_total`
  - Histograms
    - `ingestion_run_duration_seconds`
    - `ingestion_file_duration_seconds`
    - `ingestion_github_request_duration_seconds`
    - `ingestion_embedding_request_duration_seconds`
    - `ingestion_chunking_duration_seconds`
    - `ingestion_classification_duration_seconds`
    - `ingestion_db_write_duration_seconds`
    - `ingestion_file_size_bytes`
    - `ingestion_chunk_count_per_file`

  **Implementation snippet (structure):**

  ```python
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
  ```

  **Verification commands**

  ```bash
  uv --directory backend run python -c "from talkingcode.telemetry.ingestion_metrics import get_ingestion_metrics; print(type(get_ingestion_metrics()).__name__)"
  ```

  **Done criteria**

  - Ingestion metrics registry exists and imports cleanly.

- [ ] **Step 4: Instrument ingestion orchestration with detailed logs/metrics**

  **File to modify**

  - Modify: `backend/src/talkingcode/services/ingestion/ingestion_service.py`

  **Required log event names (exact strings):**

  - `ingestion.run.started`
  - `ingestion.file.started`
  - `ingestion.file.stage.completed`
  - `ingestion.file.completed`
  - `ingestion.file.failed`
  - `ingestion.run.completed`
  - `ingestion.run.failed`

  **Required log fields:**

  - `run_id`, `repository`, `git_ref`, `path` (logs only), `stage`, `duration_ms`, `status`, `error_code`

  **Implementation pattern (insert in `ingest_file`):**

  ```python
  import time
  from talkingcode.telemetry.ingestion_metrics import get_ingestion_metrics

  metrics = get_ingestion_metrics()

  file_start = time.perf_counter()
  logger.info("ingestion.file.started", run_id=str(run.id), repository=f"{repo.owner}/{repo.name}", git_ref=git_ref, path=path)

  # stage: github fetch
  t0 = time.perf_counter()
  file_content = await self.github_fetcher.fetch_file_content(...)
  fetch_sec = time.perf_counter() - t0
  metrics.ingestion_github_request_duration_seconds.record(fetch_sec, attributes={"operation": "fetch_file_content", "provider": "github"})
  logger.info("ingestion.file.stage.completed", stage="fetch", duration_ms=int(fetch_sec * 1000), path=path)

  metrics.ingestion_file_size_bytes.record(len(file_content.content.encode("utf-8")), attributes={"repository": f"{repo.owner}/{repo.name}"})

  # stage: classify
  t0 = time.perf_counter()
  classification = await self._classify_with_fallback(...)
  classify_sec = time.perf_counter() - t0
  metrics.ingestion_classification_duration_seconds.record(classify_sec, attributes={"repository": f"{repo.owner}/{repo.name}"})
  logger.info("ingestion.file.stage.completed", stage="classify", duration_ms=int(classify_sec * 1000), path=path)

  # stage: chunk
  t0 = time.perf_counter()
  chunks = self.chunker.chunk(file_content.content)
  chunk_sec = time.perf_counter() - t0
  metrics.ingestion_chunking_duration_seconds.record(chunk_sec, attributes={"repository": f"{repo.owner}/{repo.name}"})
  metrics.ingestion_chunk_count_per_file.record(len(chunks), attributes={"repository": f"{repo.owner}/{repo.name}"})
  metrics.ingestion_chunks_total.add(len(chunks), attributes={"repository": f"{repo.owner}/{repo.name}"})
  logger.info("ingestion.file.stage.completed", stage="chunk", duration_ms=int(chunk_sec * 1000), path=path, chunk_count=len(chunks))

  # stage: embed
  t0 = time.perf_counter()
  if chunks:
      embeddings = await self.embedder.embed_batch([chunk.content for chunk in chunks])
  else:
      embeddings = []
  embed_sec = time.perf_counter() - t0
  metrics.ingestion_embedding_request_duration_seconds.record(embed_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "operation": "embed_batch"})
  metrics.ingestion_embeddings_total.add(len(embeddings), attributes={"repository": f"{repo.owner}/{repo.name}"})
  logger.info("ingestion.file.stage.completed", stage="embed", duration_ms=int(embed_sec * 1000), path=path, embedding_count=len(embeddings))

  # stage: db write
  t0 = time.perf_counter()
  # existing DB save logic
  db_sec = time.perf_counter() - t0
  metrics.ingestion_db_write_duration_seconds.record(db_sec, attributes={"repository": f"{repo.owner}/{repo.name}"})
  logger.info("ingestion.file.stage.completed", stage="db_write", duration_ms=int(db_sec * 1000), path=path)

  file_sec = time.perf_counter() - file_start
  metrics.ingestion_files_total.add(1, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "success"})
  metrics.ingestion_file_duration_seconds.record(file_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "success"})
  logger.info("ingestion.file.completed", path=path, duration_ms=int(file_sec * 1000), status="success")
  ```

  **Failure branch pattern:**

  ```python
  except Exception as file_err:  # noqa: BLE001
      file_sec = time.perf_counter() - file_start
      metrics.ingestion_files_failed_total.add(1, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "failed"})
      metrics.ingestion_file_duration_seconds.record(file_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "failed"})
      logger.warning("ingestion.file.failed", path=path, duration_ms=int(file_sec * 1000), status="failed", error_code=type(file_err).__name__, error=str(file_err))
      return False
  ```

  **Run-level metrics/logs pattern:**

  ```python
  run_start = time.perf_counter()
  metrics.ingestion_runs_total.add(1, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "started"})
  logger.info("ingestion.run.started", run_id=str(run.id), repository=f"{repo.owner}/{repo.name}", git_ref=git_ref)

  # on success
  run_sec = time.perf_counter() - run_start
  metrics.ingestion_run_duration_seconds.record(run_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "done"})
  logger.info("ingestion.run.completed", run_id=str(run.id), repository=f"{repo.owner}/{repo.name}", duration_ms=int(run_sec * 1000), status="done")

  # on failure
  run_sec = time.perf_counter() - run_start
  metrics.ingestion_run_duration_seconds.record(run_sec, attributes={"repository": f"{repo.owner}/{repo.name}", "status": "failed"})
  logger.error("ingestion.run.failed", run_id=str(run.id), repository=f"{repo.owner}/{repo.name}", duration_ms=int(run_sec * 1000), status="failed", error_code=type(exc).__name__, error=str(exc))
  ```

  **Verification commands**

  ```bash
  uv --directory backend run pytest
  ```

  **Done criteria**

  - Each file ingestion path has stage timings in logs.
  - Run/file success/failure counters and durations are emitted.

- [ ] **Step 5: Instrument fetcher/embedder/classifier internals for richer metrics**

  **Files to modify**

  - Modify: `backend/src/talkingcode/services/ingestion/github_fetcher.py`
  - Modify: `backend/src/talkingcode/services/ingestion/embedder.py`
  - Modify: `backend/src/talkingcode/services/classification/document_classifier.py`

  **GitHub fetcher timing pattern:**

  ```python
  import time
  from talkingcode.telemetry.ingestion_metrics import get_ingestion_metrics

  metrics = get_ingestion_metrics()
  t0 = time.perf_counter()
  response = await client.get(...)
  elapsed = time.perf_counter() - t0
  status_class = f"{response.status_code // 100}xx"
  metrics.ingestion_github_requests_total.add(1, attributes={"operation": "fetch_file_tree", "status_class": status_class, "provider": "github"})
  metrics.ingestion_github_request_duration_seconds.record(elapsed, attributes={"operation": "fetch_file_tree", "status_class": status_class, "provider": "github"})
  ```

  **Embedder retry instrumentation pattern:**

  ```python
  t0 = time.perf_counter()
  try:
      embeddings = await self.openrouter_client.generate_embeddings(...)
      elapsed = time.perf_counter() - t0
      metrics.ingestion_embedding_requests_total.add(1, attributes={"operation": "generate_embeddings", "status": "success"})
      metrics.ingestion_embedding_request_duration_seconds.record(elapsed, attributes={"operation": "generate_embeddings", "status": "success"})
      return embeddings
  except Exception as exc:
      elapsed = time.perf_counter() - t0
      metrics.ingestion_embedding_requests_total.add(1, attributes={"operation": "generate_embeddings", "status": "failed"})
      metrics.ingestion_embedding_request_duration_seconds.record(elapsed, attributes={"operation": "generate_embeddings", "status": "failed"})
      ...
  ```

  **Classifier fallback metric increment (inside exception):**

  ```python
  metrics.ingestion_classifier_fallback_total.add(1, attributes={"operation": "classify", "status": "fallback"})
  ```

  **Verification commands**

  ```bash
  uv --directory backend run pytest
  ```

  **Done criteria**

  - GitHub and embedding requests emit latency + request counters.
  - Classifier fallback is counted.

- [ ] **Step 6: Add frontend secrets loader script (Infisical + env fallback)**

  **Files to create/modify**

  - Create: `talkingcode-frontend/scripts/secrets.js`
  - Modify: `talkingcode-frontend/package.json`
  - Modify: `talkingcode-frontend/.env.example`

  **Code pattern (full baseline):**

  ```js
  // talkingcode-frontend/scripts/secrets.js
  import 'dotenv/config';
  import { InfisicalSDK } from '@infisical/sdk';

  function isInfisicalEnabled() {
    return Boolean(process.env.INFISICAL_ENABLED);
  }

  async function loadFromInfisical() {
    const clientId = process.env.INFISICAL_CLIENT_ID;
    const clientSecret = process.env.INFISICAL_CLIENT_SECRET;
    const projectId = process.env.INFISICAL_PROJECT_ID;
    const environment = process.env.INFISICAL_ENVIRONMENT || 'prod';
    const siteUrl = process.env.INFISICAL_URL;

    if (!clientId || !clientSecret || !projectId || !siteUrl) {
      throw new Error('Missing Infisical credentials for frontend secrets loading');
    }

    const client = new InfisicalSDK({ siteUrl });
    await client.auth().universalAuth.login({ clientId, clientSecret });
    const secrets = await client.secrets().listSecrets({
      environment,
      projectId,
      includeImports: true,
    });

    const map = {};
    secrets.secrets.forEach((s) => {
      map[s.secretKey] = s.secretValue;
    });
    return map;
  }

  export async function loadFrontendSecrets() {
    let secretMap = {};
    if (isInfisicalEnabled()) {
      secretMap = await loadFromInfisical();
    }

    process.env.BACKEND_URL = process.env.BACKEND_URL || secretMap.BACKEND_URL || 'http://backend:8000';
    process.env.PUBLIC_BACKEND_URL = process.env.PUBLIC_BACKEND_URL || secretMap.PUBLIC_BACKEND_URL || process.env.BACKEND_URL;
    process.env.INGESTION_API_KEY = process.env.INGESTION_API_KEY || secretMap.INGESTION_API_KEY || '';

    process.env.OTEL_EXPORTER_OTLP_ENDPOINT = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || secretMap.OTEL_EXPORTER_OTLP_ENDPOINT || '';
    process.env.OTEL_SERVICE_NAME = process.env.OTEL_SERVICE_NAME || secretMap.OTEL_SERVICE_NAME || 'talkingcode-frontend';
    process.env.OTEL_ENVIRONMENT = process.env.OTEL_ENVIRONMENT || secretMap.OTEL_ENVIRONMENT || process.env.NODE_ENV || 'development';
  }
  ```

  **`.env.example` must include:**

  ```dotenv
  BACKEND_URL=http://localhost:8000
  PUBLIC_BACKEND_URL=http://localhost:8000
  ```

  **Verification commands**

  ```bash
  pnpm --dir talkingcode-frontend build
  ```

  **Done criteria**

  - Frontend server runtime can source secrets from env or Infisical.

- [ ] **Step 7: Add frontend OTEL instrumentation script (ReceiptToRecipe pattern) + launcher**

  **Files to create/modify**

  - Create: `talkingcode-frontend/scripts/otel-instrumentation.js`
  - Create: `talkingcode-frontend/scripts/server.js`
  - Modify: `talkingcode-frontend/package.json`

  **Use this OTEL script baseline (adapt only service defaults):**

  ```js
  import { NodeSDK } from '@opentelemetry/sdk-node';
  import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
  import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
  import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-grpc';
  import { resourceFromAttributes } from '@opentelemetry/resources';
  import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
  import { SimpleLogRecordProcessor } from '@opentelemetry/sdk-logs';
  import { logs, SeverityNumber } from '@opentelemetry/api-logs';
  import { trace, context } from '@opentelemetry/api';

  let sdk = null;
  let otelLogger = null;
  let consoleBridged = false;

  const originalConsole = {
    log: console.log.bind(console),
    info: console.info.bind(console),
    warn: console.warn.bind(console),
    error: console.error.bind(console),
    debug: console.debug.bind(console),
  };

  function bridgeConsoleLogs() {
    if (consoleBridged) return;
    const loggerProvider = logs.getLoggerProvider();
    otelLogger = loggerProvider.getLogger('console');

    const severityMap = {
      debug: SeverityNumber.DEBUG,
      log: SeverityNumber.INFO,
      info: SeverityNumber.INFO,
      warn: SeverityNumber.WARN,
      error: SeverityNumber.ERROR,
    };

    for (const [method, severity] of Object.entries(severityMap)) {
      console[method] = (...args) => {
        originalConsole[method](...args);
        if (!otelLogger) return;
        try {
          const message = args.map((arg) => (typeof arg === 'object' ? JSON.stringify(arg) : String(arg))).join(' ');
          const activeContext = context.active();
          const span = trace.getSpan(activeContext);
          const spanContext = span?.spanContext();
          otelLogger.emit({
            severityNumber: severity,
            severityText: method.toUpperCase(),
            body: message,
            timestamp: Date.now(),
            context: activeContext,
            attributes: spanContext
              ? { trace_id: spanContext.traceId, span_id: spanContext.spanId }
              : undefined,
          });
        } catch {
          // ignore
        }
      };
    }

    consoleBridged = true;
  }

  export function initTelemetry(serviceName = 'talkingcode-frontend') {
    const endpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT;
    if (!endpoint) {
      process.stdout.write('[OTel] endpoint not set; telemetry disabled\\n');
      return null;
    }

    const resource = resourceFromAttributes({
      [ATTR_SERVICE_NAME]: serviceName,
      [ATTR_SERVICE_VERSION]: process.env.npm_package_version || '0.0.1',
      'deployment.environment': process.env.OTEL_ENVIRONMENT || process.env.NODE_ENV || 'development',
    });

    const traceExporter = new OTLPTraceExporter({ url: endpoint });
    const logExporter = new OTLPLogExporter({ url: endpoint });

    sdk = new NodeSDK({
      resource,
      traceExporter,
      logRecordProcessors: [new SimpleLogRecordProcessor(logExporter)],
      instrumentations: [
        getNodeAutoInstrumentations({
          '@opentelemetry/instrumentation-fs': { enabled: false },
          '@opentelemetry/instrumentation-dns': { enabled: false },
          '@opentelemetry/instrumentation-net': { enabled: false },
        }),
      ],
    });

    sdk.start();
    bridgeConsoleLogs();
    return sdk;
  }

  export async function shutdownTelemetry() {
    if (sdk) await sdk.shutdown();
  }
  ```

  **Server launcher baseline:**

  ```js
  // talkingcode-frontend/scripts/server.js
  import { loadFrontendSecrets } from './secrets.js';
  import { initTelemetry } from './otel-instrumentation.js';

  await loadFrontendSecrets();
  initTelemetry(process.env.OTEL_SERVICE_NAME || 'talkingcode-frontend');

  await import('../build/index.js');
  ```

  **Package.json changes**

  - update `start` script to: `node scripts/server.js`
  - add OTEL dependencies used above
  - add `@infisical/sdk` and `dotenv` if not present

  **Verification commands**

  ```bash
  pnpm --dir talkingcode-frontend build
  pnpm --dir talkingcode-frontend start
  ```

  **Done criteria**

  - Frontend production runtime starts through launcher.
  - Telemetry safely no-ops when endpoint is absent.

- [ ] **Step 8: Add Python provisioning and migration scripts (ReceiptToRecipe flow)**

  **Files to create**

  - `backend/src/talkingcode/scripts/__init__.py`
  - `backend/src/talkingcode/scripts/provision_db.py`
  - `backend/src/talkingcode/scripts/migrate.py`

  **Provision script responsibilities (must all be present):**

  1. Authenticate to admin Infisical project.
  2. Authenticate to app Infisical project.
  3. If app `DATABASE_URL` exists, short-circuit success.
  4. Read admin DB creds (`POSTGRES_ADMIN_USER`, `POSTGRES_ADMIN_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`).
  5. Create database + role idempotently.
  6. Grant DB/schema privileges.
  7. Write/overwrite app `DATABASE_URL` secret.
  8. Write default config keys only if missing (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`).

  **Migrate script responsibilities:**

  1. Initialize telemetry.
  2. Run provision function.
  3. Run Alembic upgrade head.
  4. Shutdown telemetry.
  5. Exit non-zero on any failure.

  **Migration execution snippet (Python):**

  ```python
  import asyncio
  import subprocess
  import sys

  from talkingcode.scripts.provision_db import provision_database


  async def run() -> None:
      await provision_database()
      proc = subprocess.run(["uv", "run", "alembic", "upgrade", "head"], check=False)
      if proc.returncode != 0:
          raise SystemExit(proc.returncode)


  if __name__ == "__main__":
      asyncio.run(run())
  ```

  **Verification commands**

  ```bash
  uv --directory backend run python -m talkingcode.scripts.migrate
  ```

  **Done criteria**

  - Setup script is idempotent and handles existing resources cleanly.

- [ ] **Step 9: Upgrade backend and frontend Dockerfiles for production runtime**

  **Files to modify**

  - `backend/Dockerfile`
  - `talkingcode-frontend/Dockerfile`

  **Backend Dockerfile requirements:**

  - Multi-stage build.
  - Copy `pyproject.toml`, `uv.lock`, `src/`, `alembic/`, `alembic.ini`.
  - Default CMD runs app.
  - Compose setup service can override command to run migrate script.

  **Frontend Dockerfile requirements:**

  - Builder stage with `pnpm install` and `pnpm build`.
  - Runtime stage includes `build/` and `scripts/`.
  - Default CMD is `node scripts/server.js`.

  **Verification commands**

  ```bash
  docker build -f backend/Dockerfile backend
  docker build -f talkingcode-frontend/Dockerfile talkingcode-frontend
  ```

  **Done criteria**

  - Both images build and run with expected commands.

- [ ] **Step 10: Create `docker-compose.prod.yml` with setup profile and external OTLP endpoint**

  **File to create**

  - `docker-compose.prod.yml`

  **Structure requirements:**

  - `backend` app service
  - `frontend` app service
  - `backend-migrate` setup profile service (`profiles: ["setup"]`)
  - Optionally `backend-provision` setup profile service
  - Use `OTEL_EXPORTER_OTLP_ENDPOINT` env pass-through (external collector/APM)

  **Skeleton snippet:**

  ```yaml
  services:
    backend:
      image: <backend-image>
      restart: unless-stopped
      environment:
        - INFISICAL_ENABLED=${INFISICAL_ENABLED}
        - INFISICAL_CLIENT_ID=${INFISICAL_CLIENT_ID}
        - INFISICAL_CLIENT_SECRET=${INFISICAL_CLIENT_SECRET}
        - INFISICAL_PROJECT_ID=${INFISICAL_PROJECT_ID}
        - INFISICAL_ENVIRONMENT=${INFISICAL_ENVIRONMENT}
        - INFISICAL_URL=${INFISICAL_URL}
        - OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}
        - OTEL_SERVICE_NAME=talkingcode-backend

    backend-migrate:
      image: <backend-image>
      restart: "no"
      profiles: ["setup"]
      command: uv run python -m talkingcode.scripts.migrate
      environment:
        - INFISICAL_ENABLED=${INFISICAL_ENABLED}
        - INFISICAL_CLIENT_ID=${INFISICAL_CLIENT_ID}
        - INFISICAL_CLIENT_SECRET=${INFISICAL_CLIENT_SECRET}
        - INFISICAL_PROJECT_ID=${INFISICAL_PROJECT_ID}
        - INFISICAL_ENVIRONMENT=${INFISICAL_ENVIRONMENT}
        - INFISICAL_URL=${INFISICAL_URL}
        - INFISICAL_ADMIN_CLIENT_ID=${INFISICAL_ADMIN_CLIENT_ID}
        - INFISICAL_ADMIN_CLIENT_SECRET=${INFISICAL_ADMIN_CLIENT_SECRET}
        - INFISICAL_ADMIN_PROJECT_ID=${INFISICAL_ADMIN_PROJECT_ID}
        - OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}
        - OTEL_SERVICE_NAME=talkingcode-backend-migrate

    frontend:
      image: <frontend-image>
      restart: unless-stopped
      environment:
        - INFISICAL_ENABLED=${INFISICAL_ENABLED}
        - INFISICAL_CLIENT_ID=${INFISICAL_CLIENT_ID}
        - INFISICAL_CLIENT_SECRET=${INFISICAL_CLIENT_SECRET}
        - INFISICAL_PROJECT_ID=${INFISICAL_PROJECT_ID}
        - INFISICAL_ENVIRONMENT=${INFISICAL_ENVIRONMENT}
        - INFISICAL_URL=${INFISICAL_URL}
        - BACKEND_URL=http://backend:8000
        - PUBLIC_BACKEND_URL=${PUBLIC_BACKEND_URL}
        - OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT}
        - OTEL_SERVICE_NAME=talkingcode-frontend
  ```

  **Verification commands**

  ```bash
  docker compose -f docker-compose.prod.yml config
  docker compose -f docker-compose.prod.yml --profile setup up backend-migrate
  ```

  **Done criteria**

  - Config validates and setup profile can run.

- [ ] **Step 11: Create `docker-compose.dev.yml` with local services + optional collector**

  **File to create**

  - `docker-compose.dev.yml`

  **Structure requirements:**

  - `postgres` local service
  - `backend` dev service
  - `frontend` dev service
  - optional `otel-collector` service
  - optional `backend-migrate` helper

  **Dev collector snippet (optional but recommended):**

  ```yaml
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otelcol/config.yaml"]
    volumes:
      - ./deploy/otel-collector-config.yaml:/etc/otelcol/config.yaml:ro
    ports:
      - "4317:4317"
      - "4318:4318"
  ```

  **Verification commands**

  ```bash
  docker compose -f docker-compose.dev.yml config
  docker compose -f docker-compose.dev.yml up --build
  ```

  **Done criteria**

  - Local stack runs and backend health check works.

- [ ] **Step 12: Update documentation and env examples with exact required contracts**

  **Files to modify**

  - `README.md`
  - `backend/.env.example`
  - `talkingcode-frontend/.env.example`

  **Documentation must include:**

  - Runtime envs for backend/frontend.
  - Infisical required vars (app + admin for setup profile).
  - OTEL vars and behavior when omitted.
  - Setup profile usage commands.
  - Ingestion observability table (metric names and meaning).

  **Verification commands**

  ```bash
  # dry-run from docs
  docker compose -f docker-compose.dev.yml up --build
  ```

  **Done criteria**

  - A new engineer can run the system from docs only.

---

## Tests

- Backend tests:

  ```bash
  uv --directory backend run pytest
  ```

- Frontend checks:

  ```bash
  pnpm --dir talkingcode-frontend check
  pnpm --dir talkingcode-frontend build
  ```

- Compose validation:

  ```bash
  docker compose -f docker-compose.dev.yml config
  docker compose -f docker-compose.prod.yml config
  ```

---

## Final Verification Checklist

1. Backend starts with env fallback mode and Infisical mode.
2. Frontend starts through `scripts/server.js` and reads secrets.
3. OTEL is disabled cleanly when endpoint is absent.
4. OTEL exports when endpoint is present.
5. Ingestion emits:
   - run started/completed/failed logs,
   - per-stage duration logs,
   - run/file counters and duration metrics,
   - classifier fallback counters,
   - github/embed request duration metrics.
6. Prod compose setup profile runs migrate successfully.
7. Dev compose starts full local stack.
