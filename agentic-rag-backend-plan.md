# Blueprint: Agentic RAG Backend (python-swe)

## Executor Instructions

1. Read this file every loop.
2. Execute only the next unchecked step.
3. Follow `python-swe` strictly: dataclass IO models for services/controllers.
4. Verify each step before marking complete.
5. Commit each completed step.

## Context

This blueprint upgrades backend chat orchestration from a single retrieve -> generate flow to a
planner-driven agent loop with tool calls. Retrieval and file-detail lookups become tools invoked
by the model. The backend executes those tools and feeds results back to the model until stop.

The loop must be fully streamable and whitebox. Clients should receive planner/tool progress events
and filter visibility, while tool payload contents remain hidden from user-facing stream events.
Tool payloads still flow internally back into the model context.

## Scope

**In scope:**

- Planner service with strict structured output schema (runs every user turn).
- Intent classifier and retrieval filter model generation.
- Tool registry that transforms Python functions into OpenRouter tool definitions.
- Agent loop service with sequential/parallel tool execution.
- Metadata classification at ingestion (file-level -> chunk inheritance).
- Whitebox stream events and persisted tool timeline.

**Out of scope:**

- Confidence scoring subsystem.
- Live GitHub fetch fallback for file details (cache-only tool source).

## Architecture Decisions

- Service boundaries use dataclass models for inputs and outputs (no raw dict signatures).
- Tool registry uses explicit registrations tied to dataclass input/output models.
- Planner emits strict JSON (`response_format: json_schema`) with execution groups.
- Loop limits are hard-enforced (8 iterations, 3 tool calls/turn).
- Parallel execution uses `asyncio.TaskGroup` per planner-approved group only.
- Whitebox timeline is persisted with conversation history.

## Interfaces and Models

### Domain dataclasses to add

- `AgentTurnInput(conversation_id: UUID | None, question: str, selected_model: str | None)`
- `AgentTurnOutput(conversation_id: UUID, assistant_message_id: UUID, final_text: str)`
- `PlannerInput(question: str, conversation_id: UUID | None, selected_model: str | None)`
- `PlannerOutput(intent: str, filters: RetrievalFilters, tool_groups: list[ToolGroupPlan], stop_rules: StopRules)`
- `ToolGroupPlan(name: str, calls: list[PlannedToolCall], parallel: bool)`
- `PlannedToolCall(tool_name: str, arguments: dict[str, object])`
- `StopRules(max_iterations: int = 8, max_tools_per_turn: int = 3)`
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

### Service Protocols (all dataclass IO)

- `IPlannerService.plan(input: PlannerInput) -> PlannerOutput`
- `IIntentClassifier.classify(input: PlannerInput) -> PlannerOutput`
- `IToolRegistry.get_tool_definitions() -> list[OpenRouterToolDefinition]`
- `IToolRegistry.build_tool_message_result(input: ToolExecutionResult) -> ToolMessageResult`
- `IToolExecutor.execute_group(input: ExecuteToolGroupInput) -> list[ToolExecutionResult]`
- `IAgentLoopService.run_turn(input: AgentTurnInput) -> AsyncGenerator[WhiteboxEvent, None]`
- `IDocumentClassifier.classify(input: DocumentClassificationInput) -> DocumentClassificationOutput`

### Tool dataclass contracts

- `RetrieveChunksToolInput(query: str, filters: RetrievalFilters, top_k: int)`
- `RetrieveChunksToolOutput(items: list[RetrievedChunk], total: int)`
- `GetFileDetailsToolInput(repo: str, path: str, ref: str | None)`
- `GetFileDetailsToolOutput(repo: str, path: str, summary: str, symbols: list[str])`

### Tool registry rules

- Registration API requires: `name`, `description`, `input_model`, `output_model`, `callable`.
- JSON schema derives from `input_model` dataclass annotations.
- Argument decoding: dict -> dataclass instance with validation.
- Output encoding: dataclass -> JSON for tool role message.
- If decode fails, emit `ToolExecutionResult(success=False, error=...)` and continue loop.

### Structured output schemas

- Planner schema (`planner_plan_v1`):
  - required: `intent`, `filters`, `tool_groups`, `stop_rules`
  - `additionalProperties: false`, `strict: true`
- Document classifier schema (`document_classification_v1`):
  - required: `language`, `area`, `file_type`, `symbols`, `tags`
  - `area` enum locked to six values above
  - no `framework` field in schema

### Persistence additions

- Add `tool_call_events` table (recommended) or equivalent persisted structure with:
  - `id`, `conversation_id`, `message_id`, `turn_id`, `tool_name`, `visible_args_json`,
    `status`, `duration_ms`, `created_at`
- Add chunk metadata JSONB fields if missing for classification output inheritance.

## Plan

- [ ] **Step 1: Add agent loop model contracts and enums**
      Create model modules under `backend/src/talkingcode/models/` for planner/filters/tool events/
      classification/tool IO contracts listed above.
      Verify: model import/type-check smoke passes.

- [ ] **Step 2: Add persistence support for whitebox timeline and chunk metadata**
      Create ORM/repository support for `tool_call_events` and classification metadata persistence.
      Add Alembic migration for new tables/columns/indexes.
      Verify: migration applies and repository integration tests pass.

- [ ] **Step 3: Implement document classifier service (structured outputs)**
      Build `IDocumentClassifier` using OpenRouter `response_format.json_schema` strict mode.
      Input is file-level content; output is `DocumentClassificationOutput` dataclass.
      Verify: unit tests for valid schema parsing and fallback error paths.

- [ ] **Step 4: Integrate classification into ingestion pipeline**
      In pipeline ingestion flow, classify each file once and inherit metadata to all generated
      chunks from that file before persistence.
      Verify: ingestion integration test asserts inherited chunk metadata fields.

- [ ] **Step 5: Implement planner service (per-turn strict structured output)**
      Implement `IPlannerService.plan` with strict planner schema and model-fallback policy when
      selected model lacks tool/structured-output support.
      Verify: planner unit tests assert strict schema decode and fallback model path.

- [ ] **Step 6: Implement tool registry and function-to-tool transformation**
      Build registry module that turns registered Python callables + dataclass input models into
      OpenRouter tool definitions. Include decode/encode helpers and validation errors.
      Verify: unit tests for schema generation, arg decode, and dataclass output encoding.

- [ ] **Step 7: Implement tool functions for retrieval and file details**
      Implement `run_retriever` and `get_file_details_from_github` tools backed by existing
      repositories/cache only. Ensure both use dataclass input/output contracts.
      Verify: tool unit tests and repository integration tests pass.

- [ ] **Step 8: Implement tool executor with planner-group parallelism**
      Implement execution layer that takes planner groups and model-requested tool calls,
      executes allowed parallel groups with `asyncio.TaskGroup`, and enforces max 3 calls/turn.
      Verify: tests for sequential order, parallel group execution, and cap enforcement.

- [ ] **Step 9: Implement agent loop service (OpenRouter-style loop)**
      Build loop service:
      - run planner each turn,
      - call model with tools,
      - execute returned tool calls,
      - append tool messages,
      - stop on final assistant output or iteration cap.
      Verify: loop tests for stop conditions, iteration cap, and tool-call chaining.

- [ ] **Step 10: Implement whitebox streaming event emission**
      Emit `WhiteboxEvent` stream over chat endpoint showing planner/tool names/visible args and
      token stream events. Never include tool payload content in whitebox events.
      Verify: integration test asserts event ordering and payload redaction.

- [ ] **Step 11: Persist tool-call timeline per turn**
      Save whitebox timeline events in persistence layer and associate to conversation/message.
      Verify: retrieval endpoint returns timeline metadata for prior turns.

- [ ] **Step 12: Update chat controller/routes for agentic mode**
      Extend chat route/controller contracts for agent loop stream and timeline retrieval while
      keeping thin HTTP boundary and Pydantic DTO mapping.
      Verify: route contract tests and OpenAPI schema generation pass.

- [ ] **Step 13: Final backend hardening and contract verification**
      Run all backend tests; add contract checks for frontend target shapes/events.
      Verify: commands in `## Tests` pass.

## Tests

- `pytest backend/tests/unit -q -k "planner or tool_registry or agent_loop or classifier"`
- `pytest backend/tests/integration -q -k "agentic or tool_call or stream or metadata"`
- `ruff check backend/src backend/tests`

Required test cases:

- planner strict schema decoding and model fallback.
- tool registry function->schema conversion and dataclass arg parsing.
- tool executor sequential + parallel behavior using TaskGroup.
- loop stop behavior at max iterations and max tools per turn.
- document classification inheritance to chunk metadata.
- whitebox stream redaction (tool names/args visible, payload hidden).

## Verification

1. `alembic upgrade head` (from `backend/`)
2. `pytest backend/tests/unit -q -k "planner or tool_registry or agent_loop or classifier"`
3. `pytest backend/tests/integration -q -k "agentic or tool_call or stream or metadata"`
4. Start backend and run chat request that triggers tools.
5. Confirm stream events include planner/tool names/filters and no raw payload results.
