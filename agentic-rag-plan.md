# Blueprint: Agentic RAG Loop

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. Read this file at the start of every loop.
2. Execute only the next unchecked step.
3. When a step references a subplan, execute that subplan fully before returning.
4. Verify each step before checking it off.
5. Commit each completed step (`blueprint: [step title]`).
6. Keep this file and subplans updated with notes/blockers discovered during execution.

## Context

TalkingCode currently plans a classic RAG path (retrieve -> generate). This feature upgrades that
flow to an agentic tool-calling loop with explicit planning, structured classification, adaptive
tool execution, and whitebox streaming.

The target behavior is an OpenRouter-style agent loop where retrieval is a tool call, multiple
tools can run sequentially or in parallel, and the UI shows tool names and invoked filters without
showing tool payloads. The planner runs every user turn and produces strict structured output.

This blueprint is an extension to the existing V1 plans and must align with `python-swe`,
`svelte-swe`, and `svelte-ui` conventions.

## Scope

**In scope:**

- Backend agent loop orchestration with tool-calling and planner.
- Tool registry that transforms Python functions into OpenRouter tool schemas.
- Document metadata classification (structured outputs) at ingestion.
- Intent classification and retrieval filter generation before each loop.
- Whitebox streaming and persisted tool timeline.
- Frontend architecture/UI updates for tool timeline and filter visibility.

**Out of scope:**

- Tool result payload visibility in UI.
- Non-cache live GitHub detail lookups for this feature (cache only).
- Confidence scoring subsystem.

## Architecture Decisions

- Planner runs every turn with strict JSON schema output.
- Loop limits: max 8 iterations and max 3 tool calls per turn.
- Parallel policy: planner defines tool execution groups; executor uses those groups with TaskGroup.
- Model policy: selected UI model is used when compatible; fallback to configured compatible model
  for planner/tool-capable turns when needed.
- Metadata classification runs at file level and is inherited by chunks.
- `framework` classification is intentionally omitted for V1.

## Interfaces and Models

This plan delegates concrete interface/model details to subplans:

- `agentic-rag-backend-plan.md` for dataclass IO, tool registry, planner, loop events.
- `agentic-rag-frontend-plan.md` for stream event contracts and route/store mapping.
- `agentic-rag-ui-plan.md` for locked components (`svelte-ai-elements/actions`) and layout behavior.

## Plan

- [ ] **Step 1: Execute backend agentic loop blueprint**
      Complete `agentic-rag-backend-plan.md` and pass its tests/verification.
      Verify: backend subplan verification passes.

- [ ] **Step 2: Execute frontend architecture blueprint for agentic events**
      Complete `agentic-rag-frontend-plan.md` and pass its tests/verification.
      Verify: frontend architecture subplan verification passes.

- [ ] **Step 3: Execute frontend UI blueprint for whitebox agent UX**
      Complete `agentic-rag-ui-plan.md` and pass its tests/verification.
      Verify: frontend UI subplan verification passes.

- [ ] **Step 4: Run integrated agentic e2e script flow**
      Run end-to-end script checks for planner -> tool calls -> streamed answer with whitebox trace.
      Verify: all commands in `## Verification` pass.

## Tests

- Backend unit/integration tests for planner, tool registry, loop orchestration.
- Frontend service/controller/store tests for stream event handling.
- UI component tests for tool timeline/actions/filter visibility.
- Full e2e scripts for chat with tool-calling trace.

## Verification

1. `pytest backend/tests/unit -q -k "agent or planner or tool"`
2. `pytest backend/tests/integration -q -k "agentic or toolcall or stream"`
3. `pnpm --dir frontend check`
4. `pnpm --dir frontend test`
5. `pnpm --dir frontend run verify:agentic-e2e`
6. Manual sanity: ask a multi-step question and confirm:
   - planner/filter event appears,
   - tool names + args/filters appear,
   - no tool payload is shown,
   - final response streams correctly.
