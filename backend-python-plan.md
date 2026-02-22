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
- Repositories own ORM mapping and return domain models.
- Services never import each other.
- Controllers orchestrate multiple services.
- Planner uses strict structured output every turn.
- Planner fallback model is `gemini-3-flash` via OpenRouter.
- Loop limits: 8 iterations max, 3 tools/turn max.
- Parallel execution only via planner-defined groups using `asyncio.TaskGroup`.
- Chat streaming uses FastAPI SSE with named events and JSON payload data.
- SSE payload field names are `snake_case`.
- `agent_error` event payload includes: `turn_id`, `message`, optional `code`, and `timestamp`.
- Whitebox stream exposes tool names + visible args/filters only, never tool payload bodies.

## Interfaces and Models

### Core dataclasses

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

### Planner fallback policy (strict)

- Attempt planner execution with `selected_model` when provided.
- If `selected_model` is absent or cannot satisfy strict structured-output requirements, retry
  planner using OpenRouter `gemini-3-flash`.
- Fallback is planner-only behavior; tool execution and answer streaming continue in the same turn
  after a successful fallback plan.
- If fallback also fails, emit `agent_error` and end the turn cleanly (no silent downgrade to
  non-agentic behavior).

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

## Plan

- [ ] **Step 1: Scaffold backend runtime and package layout**
      Create backend project files (`pyproject.toml`, Dockerfile, env example, src/tests skeleton).
      Verify: editable install and basic imports work.

- [ ] **Step 2: Implement backend core app wiring**
      Implement `config.py`, `errors.py`, `app.py`, `dependencies.py`, `factory.py`.
      Verify: app starts and health route responds.

- [ ] **Step 3: Implement domain + ORM + Alembic foundations**
      Add domain models, ORM models, metadata wiring, and initial migration path.
      Verify: autogenerate revision works.

- [ ] **Step 4: Add repositories and baseline ingestion/search services**
      Implement repository layer and baseline services needed by tools/classification.
      Verify: repo/service tests pass.

- [ ] **Step 5: Add metadata persistence for classification and timeline**
      Add storage for chunk metadata inheritance and tool call timeline persistence.
      Verify: migration applies; repository tests for new fields/tables pass.

- [ ] **Step 6: Implement document classifier service (structured outputs)**
      File-level classification using strict JSON schema; inherit output to chunks.
      Verify: classification tests and ingestion integration tests pass.

- [ ] **Step 7: Implement planner service (every turn)**
      Planner emits strict plan object; implement fallback policy exactly as specified in
      `### Planner fallback policy (strict)`.
      Verify: planner schema and fallback tests pass.

- [ ] **Step 8: Implement tool registry (function -> tool schema)**
      Build registration, schema generation from dataclass input model, arg decoding, and output encoding.
      Verify: registry conversion/validation tests pass.

- [ ] **Step 9: Implement tools (`run_retriever`, `get_file_details_from_github`)**
      Build tools with dataclass IO; file-details uses cache only.
      Verify: tool tests pass.

- [ ] **Step 10: Implement grouped tool executor with TaskGroup**
      Execute planner groups sequentially; parallelize within marked groups; enforce 3 tools/turn cap.
      Verify: sequential/parallel/cap tests pass.

- [ ] **Step 11: Implement agent loop service**
      Build OpenRouter-style loop with tools and stop rules; planner runs every turn.
      Verify: loop chaining and iteration-cap tests pass.

- [ ] **Step 12: Implement whitebox streaming and timeline persistence**
      Emit redacted `WhiteboxEvent`s following `### Streaming contract (FastAPI SSE, wire schema)`
      and persist timeline records linked to conversation turns.
      Verify: stream ordering + redaction tests pass.

- [ ] **Step 13: Wire controllers/routes and OpenAPI contracts**
      Integrate agent loop stream and timeline retrieval into chat routes/controllers.
      Verify: API contract tests + schema generation pass; backend serves `/openapi.json`.

- [ ] **Step 14: Final backend verification**
      Run full backend test suite and fix regressions.
      Verify: all commands in `## Tests` pass.

## Tests

- `pytest backend/tests/unit -q`
- `pytest backend/tests/integration -q`
- `ruff check backend/src backend/tests`

Required focus:

- planner strict schema + model fallback,
- tool registry conversion and dataclass arg parsing,
- grouped tool execution behavior,
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
