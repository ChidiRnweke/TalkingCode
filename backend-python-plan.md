# Blueprint: TalkingCode Backend (Agentic RAG, python-swe)

## Executor Instructions

1. Read this file every loop.
2. Execute only the next unchecked step.
3. Follow `python-swe` strictly.
4. Service/controller boundaries use dataclass models for input/output.
5. Verify each step before checking it off.
6. Commit each completed step.

## Context

This backend plan builds TalkingCode around an agentic chat loop. Retrieval is executed through
tool calls, guided by a per-turn planner with structured output. File-level metadata
classification is generated during ingestion and inherited by chunks for filtered retrieval.

The prior linear retrieve -> generate path is deprecated for chat orchestration.

## Scope

**In scope:**

- Backend scaffold/core app wiring.
- Domain/ORM/repositories and migrations.
- Ingestion + classification metadata persistence.
- Planner, tool registry, tool executor, and agent loop.
- Whitebox streaming events and timeline persistence.
- Route/controller/factory integration and tests.

**Out of scope:**

- Confidence scoring subsystem.
- Live GitHub fallback in file-details tool.

## Architecture Decisions

- Dataclass IO contracts at service boundaries (no raw dict/primitive signatures).
- All domain/service IO dataclasses use `@dataclass(slots=True, frozen=True)`.
- Repositories own ORM mapping and return domain models.
- Services never import each other.
- Controllers orchestrate multiple services.
- Planner uses strict structured output every turn.
- Planner retries once on the selected/default model when strict output parsing fails, then falls
  back to `gemini-3-flash`.
- Planner fallback model is `gemini-3-flash` via OpenRouter.
- Loop limits: 8 iterations max, 3 tools/turn max.
- Tool-call timeout default is 15 seconds per call unless a specific tool override is declared.
- Parallel execution only via planner-defined groups using `asyncio.TaskGroup`.
- Chat streaming uses FastAPI SSE with named events and JSON payload data.
- SSE payload field names are `snake_case`.
- `agent_error` event payload includes: `turn_id`, `message`, optional `code`, and `timestamp`.
- Whitebox stream exposes tool names + visible args/filters only, never tool payload bodies.
- Non-blocking tool-call failures are non-fatal: they are persisted and surfaced as redacted
  failure metadata and passed back into planner context, while the turn continues.

## Interfaces and Models

### Core dataclasses

All dataclasses in this section and below are `slots=True, frozen=True`.

- `AgentTurnInput(conversation_id: UUID | None, question: str, selected_model: str | None)`
- `PlannerInput(question: str, conversation_id: UUID | None, selected_model: str | None)`
- `PlannerOutput(intent: str, filters: RetrievalFilters, tool_groups: list[ToolGroupPlan], stop_rules: StopRules)`
- `StopRules(max_iterations: int = 8, max_tools_per_turn: int = 3)`
- `ToolGroupPlan(name: str, calls: list[PlannedToolCall], parallel: bool)`
- `PlannedToolCall(tool_name: str, arguments: dict[str, object])`
- `RetrievalFilters(areas: list[Area], languages: list[str], file_types: list[FileType], path_globs: list[str], repo_scopes: list[str], symbol_hints: list[str], tags: list[str])`
- `Area` enum: `backend|frontend|infra|scripts|docs|tests`
- `FileType` enum: `source|config|migration|test|docs|ci|unknown`
- `ToolExecutionRequest(call_id: str, tool_name: str, arguments: dict[str, object])`
- `ToolExecutionResult(call_id: str, tool_name: str, success: bool, payload_json: str, duration_ms: int, error: str | None)`
- `WhiteboxEvent(kind: WhiteboxEventKind, turn_id: str, tool_name: str | None, message: str, visible_args: dict[str, object] | None, timestamp: datetime)`
- `WhiteboxEventKind` enum:
  `planner_started|planner_ready|tool_call_started|tool_call_finished|assistant_token|assistant_done|agent_error`
- `DocumentClassificationInput(repo: str, path: str, content: str)`
- `DocumentClassificationOutput(language: str, area: Area, file_type: FileType, symbols: list[str], tags: list[str])`

### Tool IO dataclasses

- `RetrieveChunksToolInput(query: str, filters: RetrievalFilters, top_k: int)`
- `RetrieveChunksToolOutput(items: list[RetrievedChunk], total: int)`
- `GetFileDetailsToolInput(repo: str, path: str, ref: str | None)`
- `GetFileDetailsToolOutput(repo: str, path: str, summary: str, symbols: list[str])`

### Service Protocols

- `IPlannerService.plan(input: PlannerInput) -> PlannerOutput`
- `IDocumentClassifier.classify(input: DocumentClassificationInput) -> DocumentClassificationOutput`
- `IToolRegistry.get_tool_definitions() -> list[OpenRouterToolDefinition]`
- `IToolExecutor.execute_group(input: ExecuteToolGroupInput) -> list[ToolExecutionResult]`
- `IAgentLoopService.run_turn(input: AgentTurnInput) -> AsyncGenerator[WhiteboxEvent, None]`

### Structured output schemas

- `planner_plan_v1` strict schema with required: `intent`, `filters`, `tool_groups`, `stop_rules`.
- `document_classification_v1` strict schema with required:
  `language`, `area`, `file_type`, `symbols`, `tags`.
- No `framework` field.
- OpenAPI emitted by backend is the canonical frontend contract source and must be retrievable at
  `http://localhost:8000/openapi.json` when backend is running.

### Route contracts (V1)

- `POST /chat/agentic`
  - request body maps to `AgentTurnInput`
  - response is SSE stream conforming to `### Streaming contract (FastAPI SSE, wire schema)`
- `GET /chat/timeline?conversation_id=<uuid>`
  - response is redacted timeline metadata only (tool name, visible args, status, duration,
    timestamps, and safe error metadata)
  - no raw tool payload bodies are returned

### Persistence schema (V1, full detail)

### ETL and retrieval schema (V1, full detail)

The implementation must include explicit ingestion/retrieval persistence beyond turn/timeline
tracking. Minimum required tables and constraints:

- `repositories`
  - `id` (UUID, PK)
  - `provider` (`github`)
  - `owner` (text)
  - `name` (text)
  - `default_branch` (text)
  - `last_ingested_at` (timestamptz, nullable)
  - `created_at` (timestamptz)
  - unique `(provider, owner, name)`
- `documents`
  - `id` (UUID, PK)
  - `repository_id` (UUID, FK to `repositories.id`)
  - `path` (text)
  - `git_ref` (text)
  - `content_sha` (text)
  - `language` (text)
  - `area` (enum/text aligned to `Area`)
  - `file_type` (enum/text aligned to `FileType`)
  - `symbols_json` (jsonb)
  - `tags_json` (jsonb)
  - `created_at` (timestamptz)
  - `updated_at` (timestamptz)
  - unique `(repository_id, path, git_ref)`
- `document_chunks`
  - `id` (UUID, PK)
  - `document_id` (UUID, FK to `documents.id`)
  - `chunk_index` (int)
  - `content` (text)
  - `token_count` (int)
  - inherited metadata fields: `language`, `area`, `file_type`, `symbols_json`, `tags_json`
  - `start_line` (int, nullable)
  - `end_line` (int, nullable)
  - `created_at` (timestamptz)
  - unique `(document_id, chunk_index)`
- `chunk_embeddings`
  - `id` (UUID, PK)
  - `chunk_id` (UUID, FK to `document_chunks.id`, unique)
  - `embedding_model` (text)
  - `embedding` (vector)
  - `created_at` (timestamptz)
- `ingestion_runs`
  - `id` (UUID, PK)
  - `repository_id` (UUID, FK to `repositories.id`)
  - `status` (`running | done | failed`)
  - `started_at` (timestamptz)
  - `completed_at` (timestamptz, nullable)
  - `error_message` (text, nullable)

Required indexes for retrieval:

- `(repository_id, path)` on `documents`
- `(area, file_type)` on `document_chunks`
- GIN index for `symbols_json` and `tags_json` on `document_chunks`
- vector index on `chunk_embeddings.embedding` suitable for pgVector similarity search

- `conversation_turns` table:
  - `id` (UUID, PK)
  - `conversation_id` (UUID, FK)
  - `question` (text)
  - `selected_model` (text, nullable)
  - `planner_model_used` (text)
  - `status` (`done | error`)
  - `created_at` (timestamptz)
  - `completed_at` (timestamptz, nullable)
- `tool_call_timeline` table:
  - `id` (UUID, PK)
  - `turn_id` (UUID, FK to `conversation_turns.id`)
  - `sequence_no` (int)
  - `group_name` (text)
  - `tool_name` (text)
  - `visible_args_json` (jsonb)
  - `status` (`started | finished | failed`)
  - `success` (bool, nullable)
  - `duration_ms` (int, nullable)
  - `error_code` (text, nullable)
  - `error_message` (text, nullable)
  - `created_at` (timestamptz)
- Required indexes:
  - `(turn_id, sequence_no)` on `tool_call_timeline`
  - `(conversation_id, created_at)` on `conversation_turns`
- Optional (disabled by default for V1): `tool_call_payload_cache`
  - `id` (UUID, PK)
  - `timeline_id` (UUID, FK to `tool_call_timeline.id`)
  - `payload_json_encrypted` (text/jsonb)
  - `ttl_expires_at` (timestamptz)
  - Never exposed in API responses or SSE events.

### Tool contract enforcement (V1)

- Tool registry schemas are generated from dataclass tool IO models.
- Argument decoding is strict: unknown arguments fail validation.
- Execution policy defaults to blocking:
  - if a tool call fails, the current execution group stops,
  - subsequent groups are skipped,
  - an `agent_error` is emitted with a safe message.
- Non-blocking calls are allowed only when explicitly flagged in the planner output.
- Non-blocking call failures:
  - do not stop the execution group,
  - are recorded in `tool_call_timeline` with failure metadata,
  - are included in planner/tool-context summaries as redacted failure signals,
  - do not expose raw payload content.

### Planner fallback policy (strict)

- Attempt planner execution with `selected_model` when provided.
- If strict output parsing fails on the selected/default model, retry once on that same model.
- If that retry fails (or no selected model is provided and default fails), retry planner using
  OpenRouter `gemini-3-flash`.
- Fallback is planner-only behavior; tool execution and answer streaming continue in the same turn
  after a successful fallback plan.
- If fallback also fails, emit `agent_error` and end the turn cleanly (no silent downgrade to
  non-agentic behavior).

### Tool timeout policy (V1)

- Default timeout is 15 seconds per tool call.
- A tool may declare an explicit timeout override in registry metadata.
- Timeout is treated as a tool failure and follows blocking/non-blocking policy by call mode.

### Streaming contract (FastAPI SSE, wire schema)

- Response media type: `text/event-stream`.
- Event framing: named SSE events using `event: <name>` and `data: <json>`.
- Event names are exactly:
  - `planner_started`
  - `planner_ready`
  - `tool_call_started`
  - `tool_call_finished`
  - `assistant_token`
  - `assistant_done`
  - `agent_error`
- JSON payload keys are `snake_case`.
- Minimum event payload contract:
  - `planner_started`: `{ "turn_id": str, "timestamp": str }`
  - `planner_ready`: `{ "turn_id": str, "intent": str, "filters": object, "timestamp": str }`
  - `tool_call_started`: `{ "turn_id": str, "tool_name": str, "visible_args": object, "timestamp": str }`
  - `tool_call_finished`: `{ "turn_id": str, "tool_name": str, "success": bool, "duration_ms": int, "timestamp": str }`
  - `assistant_token`: `{ "turn_id": str, "token": str, "timestamp": str }`
  - `assistant_done`: `{ "turn_id": str, "timestamp": str }`
  - `agent_error`: `{ "turn_id": str, "message": str, "code": str | null, "timestamp": str }`
- Never include raw tool payload bodies in any event.
- Frontend-facing stream/timeline surfaces only tool names, visible args, statuses, and timings.

## Plan

- [x] **Step 1: Scaffold backend runtime and package layout**
      Created backend project with `uv init`, dependencies installed via `uv add`.
      Verify: editable install and basic imports work.

- [x] **Step 2: Implement backend core app wiring**
      Implemented `config.py` (AppConfig.from_env), `errors.py` (error hierarchy), `app.py` (FastAPI app),
      `dependencies.py` (FastAPI Depends), `factory.py` (AppFactory dataclass).
      Verify: app starts and health route responds.

- [ ] **Step 3: Implement domain + ORM + Alembic foundations**
      Added domain dataclasses (slots=True, frozen=True), ORM models in `models/orm.py`
      (repositories, documents, chunks, embeddings, conversation_turns, timeline).
      Verify: autogenerate revision works.

- [ ] **Step 4: Add repositories and baseline ingestion/search services**
      Implemented ConversationRepository, DocumentRepository with search and save methods.
      Verify: repo methods work with ORM.

- [ ] **Step 5: Add metadata persistence for classification and timeline**
      Added TimelineRepository for tool call timeline persistence.
      Verify: timeline CRUD works.

- [ ] **Step 6: Implement document classifier service (structured outputs)**
      DocumentClassifier with OpenAI structured outputs, strict JSON schema for classification.
      Verify: classification service returns proper output.

- [ ] **Step 7: Implement planner service (every turn)**
      PlannerService with OpenRouter integration, strict structured output schema,
      fallback policy: one retry then gemini-3-flash fallback.
      Verify: planner schema and fallback behavior work.

- [ ] **Step 8: Implement tool registry (function -> tool schema)**
      ToolRegistry with register_tool, get_tool_definitions, execute_group with TaskGroup.
      Verify: registry converts and executes tools.

- [ ] **Step 9: Implement tools (`run_retriever`, `get_file_details_from_github`)**
      RetrieverTool with dataclass IO, schema generation, cache-only file details.
      Verify: tool execution works.

- [ ] **Step 10: Implement grouped tool executor with TaskGroup**
      execute_group in ToolRegistry with sequential/parallel execution using TaskGroup,
      3 tools/turn cap enforced.
      Verify: parallel execution works, failures handled properly.

- [ ] **Step 11: Implement agent loop service**
      AgentLoopService with run_turn async generator, planner every turn, stop rules enforcement.
      Verify: loop streams events correctly.

- [ ] **Step 12: Implement whitebox streaming and timeline persistence**
      WhiteboxEvent streaming with all event types, timeline entries created during execution.
      Verify: stream ordering correct, payload bodies hidden.

- [ ] **Step 13: Wire controllers/routes and OpenAPI contracts**
      ChatController with start_agentic_turn and get_timeline, FastAPI routes at /chat/agentic
      (SSE) and /chat/timeline.
      Verify: API serves OpenAPI spec at /openapi.json.

- [ ] **Step 14: Final backend verification**
      All backend components integrated, docker-compose configured.
      Verify: docker compose config succeeds, health endpoint responds.

## Tests

- `pytest backend/tests/unit -q`
- `pytest backend/tests/integration -q`
- `ruff check backend/src backend/tests`

Required focus:

- planner strict schema + model fallback,
- planner one-retry-then-fallback behavior,
- tool registry conversion and dataclass arg parsing,
- grouped tool execution behavior,
- tool timeout behavior (default + overrides),
- non-blocking failure continuation + redacted failure propagation,
- loop stop conditions,
- classification inheritance,
- whitebox payload redaction.

## Verification

1. `alembic upgrade head` (from `backend/`)
2. `pytest backend/tests/unit -q`
3. `pytest backend/tests/integration -q`
4. Start backend and run a tool-calling chat turn.
5. `curl -fsS http://localhost:8000/openapi.json -o /tmp/talkingcode-openapi.json`
6. `test -s /tmp/talkingcode-openapi.json`
7. Confirm planner/tool whitebox events stream and payload bodies are hidden.
