# Blueprint: TalkingCode Frontend Architecture (Agentic RAG, svelte-swe)

## Executor Instructions

1. Read this file every loop.
2. Execute only the next unchecked step.
3. Keep strict `svelte-swe` layering.
4. Verify each step before checking off.
5. Commit each completed step.

## Context

This frontend plan implements architecture for agentic streaming chat: planner events, tool call
timeline, visible filters, and final token stream. The legacy non-agentic flow is deprecated.

## Scope

**In scope:**

- Typed API client generation and service mapping.
- Agentic stream event models and parsers.
- Controller orchestration for turn start + timeline replay.
- Route contract mapping and store state transitions.
- Agentic e2e verification scripts.

**Out of scope:**

- Visual styling specifics (handled by `frontend-ui-plan.md`).

## Architecture Decisions

- Services parse SSE and expose domain events only.
- Route handlers stay thin; controllers/services own orchestration.
- UI never receives raw tool payload content.
- Chat route/UI composition follows locked inventory from `frontend-ui-plan.md`.

## Interfaces and Models

### Required domain contracts (`src/lib/models`)

- `AgenticAskInput { conversationId: string | null; question: string; model: string | null }`
- `AgentPlanView { intent: string; filters: RetrievalFilterView; toolGroups: ToolGroupView[] }`
- `RetrievalFilterView { areas: Area[]; languages: string[]; fileTypes: FileType[]; pathGlobs: string[]; repoScopes: string[]; symbolHints: string[]; tags: string[] }`
- `ToolCallTimelineItem { turnId: string; toolName: string; visibleArgs: Record<string, unknown>; status: 'started' | 'finished' | 'failed'; durationMs?: number; timestamp: string }`
- `AgentStreamEvent` variants:
  - `planner_started`
  - `planner_ready`
  - `tool_call_started`
  - `tool_call_finished`
  - `assistant_token`
  - `assistant_done`
  - `agent_error`
- `Area` union: `'backend' | 'frontend' | 'infra' | 'scripts' | 'docs' | 'tests'`
- `FileType` union: `'source' | 'config' | 'migration' | 'test' | 'docs' | 'ci' | 'unknown'`

### Service interfaces (`src/lib/services`)

- `IChatService.askAgentic(input: AgenticAskInput): AsyncIterable<AgentStreamEvent>`
- `IChatService.getToolTimeline(conversationId: string): Promise<ToolCallTimelineItem[]>`

### Controller contracts (`src/lib/controllers`)

- `ChatController.startAgenticTurn(input: AgenticAskInput): AsyncIterable<AgentStreamEvent>`
- `ChatController.loadToolTimeline(input: { conversationId: string }): Promise<ToolCallTimelineItem[]>`

### Route contract map

- `/` `load()` returns:
  - `conversations`,
  - `activeConversation`,
  - `timeline`,
  - `modelOptions`,
  - `selectedModel`.
- `/` chat action/endpoint consumes `AgenticAskInput` and streams `AgentStreamEvent`.

## Plan

- [ ] **Step 1: Scaffold/update frontend package and typed API tooling**
      Ensure scripts and OpenAPI generation are configured and stable.
      Verify: install/check/generate scripts pass.

- [ ] **Step 2: Implement domain models and service/controller interfaces**
      Add the contracts in `## Interfaces and Models`.
      Verify: type-check passes.

- [ ] **Step 3: Implement chat service SSE parser for agentic events**
      Parse backend stream into typed events and reject payload-leak fields.
      Verify: parser tests for all variants and malformed chunks.

- [ ] **Step 4: Implement controller orchestration for turn + timeline**
      Add controller methods for starting a turn and loading history timeline.
      Verify: controller tests with mocked services.

- [ ] **Step 5: Wire route loaders/actions to locked contracts**
      Update route server modules to return only route contract shapes.
      Verify: route type tests/smoke tests pass.

- [ ] **Step 6: Implement store state machine for agentic turn lifecycle**
      Add per-turn states: planning -> tools -> streaming -> done/error.
      Verify: store transition tests pass.

- [ ] **Step 7: Add agentic e2e verification scripts**
      Add `verify:agentic-e2e` to validate event ordering and UI-facing payload privacy.
      Verify: script passes against running backend.

- [ ] **Step 8: Final architecture audit**
      Confirm no layer violations and no transport schema leaks.
      Verify: all tests/checks pass.

## Tests

- `pnpm --dir frontend check`
- `pnpm --dir frontend test`
- `pnpm --dir frontend run generate:api`
- `pnpm --dir frontend run verify:agentic-e2e`

## Verification

1. Start backend + frontend.
2. Run all commands in `## Tests`.
3. Ask a question and confirm planner/tool events render while response streams.
