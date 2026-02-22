# Blueprint: ReAct Iterative Agent Loop with Live Plan/Tools Streaming

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. **Read this file first.** Every loop, re-read this file before doing anything.
   After context compaction, this file is your ground truth.
2. **Do the next unchecked step.** Find the first `- [ ]` item. Do that. Only that.
3. **Verify before checking off.** Run the verification described in the step.
   If it passes, change `- [ ]` to `- [x]` and commit.
4. **Commit after each step.** `git add -A && git commit -m "blueprint: [step title]"`
5. **Don't skip ahead.** Steps are ordered by dependency.
6. **Follow existing patterns.** Match repository/service/controller/factory patterns already used in TalkingCode.
7. **If stuck, document and move on.** Add a note under the blocked step and continue.
8. **Update this file.** Keep this blueprint as the single source of truth.

---

## Context

TalkingCode currently runs a planner-first backend flow where `PlannerService` returns `tool_groups`
and `AgentLoopService` executes those groups before streaming assistant tokens. This exists in
`backend/src/talkingcode/services/agent/agent_loop.py`,
`backend/src/talkingcode/services/planner/planner_service.py`, and
`backend/src/talkingcode/services/tools/tool_registry.py`.

The project goal is a full ReAct iterative loop: model decides tool calls step-by-step, tool
observations are fed back into the model, and iterations continue until final answer or stop rules.
Parallel tool calls must be supported in the same iteration. Frontend must receive and render live
plan/tool progress while the turn is still streaming.

Frontend currently parses SSE in `talkingcode-frontend/src/lib/services/ChatService.ts` but does
not perform strict payload validation. Unknown event types are ignored, but unknown/missing fields
are tolerated through permissive defaults. This must be replaced by strict schema validation and
incremental UI rendering for plan and tool activity.

## Scope

**In scope:**

- Replace planner-first `/chat/agentic` backend flow with full ReAct iterative loop
- Keep and improve parallel tool call execution in iterations
- Stream plan text/chunks and tool lifecycle to frontend over SSE
- Add strict backend tool contract validation (unknown tool, args schema, timeout)
- Add strict frontend SSE payload validation and live rendering updates
- Deprecate/delete planner-first code paths not used by `/chat/agentic`
- Add backend + frontend tests for the new contract

**Out of scope:**

- Visual redesign of the chat UI
- Multi-agent orchestration beyond one ReAct executor
- Infrastructure/deployment changes

## Architecture Decisions

1. `/chat/agentic` becomes ReAct-iterative and no longer depends on planner-generated `tool_groups`.
2. SSE stays the transport. Plan/tool progress is represented as structured events (not HTML tags).
   Frontend can still render this as plan/tool panels while streaming.
3. Tool execution keeps `TaskGroup` parallelism. Contract validation is done before execution.
4. Frontend parser uses strict runtime schemas (zod) and rejects unknown or malformed payloads.
5. Planner-first artifacts are deprecated for `/chat/agentic` and removed once references are gone.

## Interfaces and Models

Backend event model (SSE kinds):

- `iteration_started` `{ turn_id, iteration, timestamp }`
- `plan_chunk` `{ turn_id, iteration, chunk, timestamp }`
- `plan_done` `{ turn_id, iteration, plan_text, timestamp }`
- `tool_call_started` `{ turn_id, iteration, call_id, tool_name, visible_args, timestamp }`
- `tool_call_finished` `{ turn_id, iteration, call_id, tool_name, success, duration_ms, error_code?, timestamp }`
- `assistant_token` `{ turn_id, token, timestamp }`
- `assistant_done` `{ turn_id, timestamp }`
- `agent_error` `{ turn_id, code, message, timestamp }`

Backend stable contract error codes:

- `unknown_tool`
- `invalid_tool_arguments`
- `tool_timeout`
- `malformed_model_output`
- `iteration_limit_reached`

Frontend state extensions:

- Track `planText` progressively from `plan_chunk` and finalize on `plan_done`
- Track tool calls by `(turnId, callId)` instead of `(turnId, toolName)`
- Render iteration-aware tool activity

## Plan

- [ ] **Step 1: Introduce ReAct SSE event and contract models across backend + frontend**
      Add new event enums/types (`iteration_started`, `plan_chunk`, `plan_done`) and call identity
      fields (`call_id`, `iteration`) in backend and frontend model contracts without changing the
      execution loop yet. Keep code compiling while both old and new event kinds are representable.
      Files: `backend/src/talkingcode/enums.py`, `backend/src/talkingcode/domain/models.py`,
      `talkingcode-frontend/src/lib/models/index.ts`.
      Verify: backend and frontend type checks pass.

- [ ] **Step 2: Add strict tool contract validation and timeout enforcement in ToolRegistry**
      Validate tool existence and arguments against registered schemas before execution. Enforce
      per-call timeout with `asyncio.wait_for`. Return structured error codes.
      Pattern reference: existing `ToolRegistry` execution path.
      Verify: new backend unit tests for unknown tools, invalid args, timeout.

- [ ] **Step 3: Implement iterative ReAct loop in AgentLoopService with parallel tool batches**
      Refactor `AgentLoopService` to run iterative model-tool-observation cycles until completion.
      Emit new iteration/plan/tool events and preserve final assistant token streaming.
      Pattern reference: existing event streaming + timeline persistence in current loop.
      Verify: integration test for multi-iteration turn with parallel tool calls.

- [ ] **Step 4: Extend OpenRouter client adapter for structured tool-call round trips**
      Add API surface to send tools and parse assistant outputs containing tool calls + plan text.
      Verify: adapter tests for structured extraction and malformed output handling.

- [ ] **Step 5: Update chat controller/routes/timeline to the ReAct contract**
      Keep endpoint shape (`/chat/agentic`) but emit new contract payloads. Ensure timeline persists
      `call_id` and iteration context and retrieval reflects those fields.
      Verify: route-level stream contract tests and timeline response tests.

- [ ] **Step 6: Implement strict frontend SSE parsing and incremental rendering**
      Replace permissive parsing in `ChatService` with zod schema validation per event kind.
      Update store and domain components to render plan and tool progress live.
      Verify: frontend unit tests for valid/invalid payloads and store transitions.

- [ ] **Step 7: Deprecate and delete planner-first artifacts for /chat/agentic**
      Remove unused planner-first logic/events from the active chat path and associated dead code.
      Keep only what is still needed outside `/chat/agentic`.
      Verify: grep confirms no planner-first dependency in active agentic endpoint path.

- [ ] **Step 8: End-to-end verification and blueprint updates**
      Run backend and frontend test suites, update this blueprint with any execution notes,
      and ensure all steps are checked with evidence.
      Verify: `uv run pytest backend/tests -q` and `pnpm --dir talkingcode-frontend test:unit`.

## Tests

- Backend unit tests
  - Tool contract validation: unknown tool, invalid args, timeout
  - Event and error code mapping
- Backend integration tests
  - Iterative loop with parallel tool calls and final completion
- Frontend unit tests
  - Strict SSE parser (unknown event/field/type/missing field rejection)
  - Store updates for `plan_chunk`, `plan_done`, `tool_call_started`, `tool_call_finished`

Commands:

- `uv run pytest backend/tests -q`
- `pnpm --dir talkingcode-frontend test:unit`

## Verification

After all steps are complete:

1. Start backend + frontend locally.
2. Send one question that requires multiple tool calls.
3. Confirm UI shows plan text as it streams and tool calls update live.
4. Confirm at least one iteration executes parallel tool calls.
5. Confirm final assistant answer streams after tool observations.
6. Confirm malformed tool calls return stable contract errors without crashing the turn.
