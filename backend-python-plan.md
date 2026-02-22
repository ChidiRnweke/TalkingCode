# Blueprint: TalkingCode Backend (python-swe)

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. Read this file at the start of every loop.
2. Execute the next unchecked step only.
3. Follow `python-swe` architecture and `AGENTS.md` conventions.
4. Verify each step before checking it off.
5. Commit each completed step with `blueprint: [step title]`.
6. If blocked, leave a short blocker note under that step and continue when possible.

## Context

This subplan builds the FastAPI backend for TalkingCode V1 using strict layered architecture.
The backend must ingest public GitHub repositories, chunk and embed code with OpenAI embeddings,
store vectors in Postgres+pgVector, and stream chat responses grounded in retrieved code.

The repository is effectively greenfield for implementation code, so this plan establishes canonical
patterns for all backend layers early: Protocol-first interfaces, dataclass implementations,
repository-owned ORM mappings, controller orchestration, and factory-based dependency assembly.

This plan is dependency input to `PLAN.md` and must reach API-ready, test-verified state before
frontend architecture work depends on it.

## Scope

**In scope:**

- Backend project scaffold (`pyproject.toml`, src layout, env examples, Dockerfile).
- Core app bootstrap (`config.py`, `errors.py`, `app.py`, `dependencies.py`, `factory.py`).
- Domain models, ORM models, Alembic setup, and initial migration with vector extension.
- Repositories, services, controllers, routes, and pipeline runner.
- Unit/integration tests for critical behavior and route smoke checks.

**Out of scope:**

- Auth stack and user identity management.
- Private repo ingestion permissions workflow.
- Non-essential feature extras (reranking, semantic cache, observability platform).

## Architecture Decisions

- Use `@dataclass(slots=True, frozen=True)` for service/controller/factory implementations.
- Use Protocols for repository/service interfaces; avoid ABC inheritance.
- ORM models live only in repository layer; domain dataclasses are returned upward.
- Services never import each other; composition happens via constructor injection and controllers.
- Controllers orchestrate multi-service workflows; routes stay thin and HTTP-focused.
- Error hierarchy stays domain-level; HTTP status mapping occurs at FastAPI edge only.
- OpenAI is required embedding provider.

## Interfaces and Models

Core interfaces/models expected:

- Models: `Repository`, `CodeChunk`, `RankedChunk`, `Conversation`, `Message`, `PipelineRun`.
- Repositories: `IRepositoryRepo`, `ICodeChunkRepo`, `IConversationRepo`, `IPipelineRunRepo`.
- Services: `IGitHubService`, `IEmbeddingService`, `IChunkingService`, `ISearchService`,
  `ILLMService`, `IChatService`, `IPipelineService`.
- Controllers: chat/repo/pipeline/settings orchestration dataclasses.

## Plan

- [ ] **Step 1: Create backend project scaffold and dependencies**
      Create `backend/pyproject.toml`, `backend/Dockerfile`, `backend/.env.example`, `backend/tests`
      structure, and `backend/src/talkingcode/` package roots. Include async FastAPI, SQLAlchemy,
      Alembic, pgvector, OpenAI client, structlog, pytest, and lint/test tooling dependencies.
      Verify: `python -m pip install -e backend` succeeds.

- [ ] **Step 2: Implement config, error hierarchy, and app bootstrap**
      Create `backend/src/talkingcode/config.py`, `errors.py`, `app.py`, `dependencies.py`.
      Implement `AppConfig.from_env()` with required env validation and async engine/session maker.
      Add centralized error mapping in app handlers and include route modules under `/api`.
      Verify: backend starts with valid env and `curl http://localhost:8000/api/health` returns ok.

- [ ] **Step 3: Add factory skeleton and dependency assembly points**
      Create `backend/src/talkingcode/factory.py` with repository/service/controller factory methods
      (placeholders allowed initially), request-scoped via session + config dependency.
      Verify: app imports and starts without factory resolution errors.

- [ ] **Step 4: Implement domain and ORM models with Alembic wiring**
      Add dataclasses under `backend/src/talkingcode/models/` and ORM models under
      `backend/src/talkingcode/repositories/orm/` including `Vector(1536)` embedding field.
      Configure `alembic.ini` + `alembic/env.py` with metadata discovery through ORM package import.
      Verify: `alembic revision --autogenerate -m "initial_schema"` succeeds.

- [ ] **Step 5: Apply initial migration with vector extension**
      Edit migration to execute `CREATE EXTENSION IF NOT EXISTS vector;` and apply it.
      Validate table creation, FK constraints, and key indexes.
      Verify: `alembic upgrade head` and `\dt` shows expected tables.

- [ ] **Step 6: Implement repository layer end-to-end**
      Implement Protocol + concrete classes in `backend/src/talkingcode/repositories/` for repo,
      chunk, conversation, and pipeline runs. Add domain mapping helpers and exception wrapping.
      Implement chunk similarity search via pgvector cosine distance + repo join metadata.
      Verify: repository integration tests pass.

- [ ] **Step 7: Implement ingestion/retrieval service layer**
      Implement GitHub, embedding, chunking, and search services in
      `backend/src/talkingcode/services/` with module-level structlog loggers, retries,
      and bounded concurrency where needed.
      Verify: service unit tests for happy path + error path pass.

- [ ] **Step 8: Implement LLM and chat orchestration services**
      Implement OpenRouter streaming parser in LLM service and chat orchestration flow that stores
      user/assistant messages, retrieves context, and emits stream chunks.
      Verify: unit tests for streaming parse and chat orchestration pass.

- [ ] **Step 9: Implement pipeline orchestration and CLI runner**
      Implement pipeline ingestion workflow service and
      `backend/src/talkingcode/pipeline/runner.py` entrypoint.
      Ensure run status persists on success and failure.
      Verify: runner command executes and writes pipeline run records.

- [ ] **Step 10: Implement controllers and routes with thin HTTP boundary**
      Create `backend/src/talkingcode/controllers/*.py` and `routes/*.py` for health/chat/repos/
      pipeline/settings. Use Pydantic schemas in route modules and delegate orchestration fully.
      Verify: endpoint smoke curls pass for each route group.

- [ ] **Step 11: Finalize factory wiring and backend test suite**
      Replace remaining factory placeholders with concrete assembly for all repositories,
      services, and controllers. Run unit + integration suites and fix cross-layer issues.
      Verify: commands in `## Tests` pass.

## Tests

- `pytest backend/tests/unit -q`
- `pytest backend/tests/integration -q`
- `ruff check backend/src backend/tests`

Minimum behavior coverage:

- Repository CRUD and mapping behavior.
- Chunk similarity search behavior and ranking shape.
- Service error mapping for GitHub/OpenAI/OpenRouter failures.
- Chat persistence + streaming orchestration.
- Pipeline status transitions (running/completed/failed).

## Verification

1. `docker compose up -d postgres`
2. `alembic upgrade head` (from `backend/`)
3. `uvicorn talkingcode.app:app --host 0.0.0.0 --port 8000 --reload` (from `backend/`)
4. `curl http://localhost:8000/api/health`
5. `pytest backend/tests/unit -q`
6. `pytest backend/tests/integration -q`
7. Route smoke checks:
   - `curl http://localhost:8000/api/repos`
   - `curl -X POST http://localhost:8000/api/repos/sync`
   - `curl http://localhost:8000/api/pipeline/status`
