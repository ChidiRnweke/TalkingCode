# Blueprint: Agentic RAG Frontend Architecture (svelte-swe)

## Executor Instructions

1. Read this file every loop.
2. Execute only the next unchecked step.
3. Keep strict svelte-swe layer separation.
4. Verify each step before checking off.
5. Commit each completed step.

## Context

This blueprint adds frontend architecture support for backend agentic streaming: planner events,
tool call lifecycle events, filters visibility, and final assistant token stream.

The UI must show whitebox process state while hiding tool payload data. Route/server/service/store
contracts must be explicit and stable for executor reliability.

## Scope

**In scope:**

- Typed stream event contracts and service parsing.
- Controller orchestration for agentic chat flow.
- Route loader/action contracts for timeline and whitebox filters.
- Store state for active turn and persisted timeline replay.
- Frontend e2e scripts validating agentic event flow.

**Out of scope:**

- Visual styling details (handled in `agentic-rag-ui-plan.md`).

## Architecture Decisions

- Services parse SSE and expose domain events only.
- Controllers orchestrate chat turn + timeline fetch; components remain UI-only.
- Route contracts are locked to avoid drift from UI component contract table.
- Tool payload data is never propagated to UI models.

## Interfaces and Models

### Domain interfaces to add/update (`frontend/src/lib/models`)

- `AgenticAskInput { conversationId: string | null; question: string; model: string | null }`
- `AgentPlanView { intent: string; filters: RetrievalFilterView; toolGroups: ToolGroupView[] }`
- `RetrievalFilterView { areas: Area[]; languages: string[]; fileTypes: FileType[]; pathGlobs: string[]; repoScopes: string[]; symbolHints: string[]; tags: string[] }`
- `ToolCallTimelineItem { turnId: string; toolName: string; visibleArgs: Record<string, unknown>; status: 'started' | 'finished' | 'failed'; durationMs?: number; timestamp: string }`
- `AgentStreamEvent`
  - `{ kind: 'planner_started'; turnId: string }`
  - `{ kind: 'planner_ready'; turnId: string; plan: AgentPlanView }`
  - `{ kind: 'tool_call_started'; item: ToolCallTimelineItem }`
  - `{ kind: 'tool_call_finished'; item: ToolCallTimelineItem }`
  - `{ kind: 'assistant_token'; turnId: string; token: string }`
  - `{ kind: 'assistant_done'; turnId: string; messageId: string }`
  - `{ kind: 'agent_error'; turnId: string; message: string }`
- `Area` union: `'backend' | 'frontend' | 'infra' | 'scripts' | 'docs' | 'tests'`
- `FileType` union: `'source' | 'config' | 'migration' | 'test' | 'docs' | 'ci' | 'unknown'`

### Service interfaces (`frontend/src/lib/services`)

- `IChatService.askAgentic(input: AgenticAskInput): AsyncIterable<AgentStreamEvent>`
- `IChatService.getToolTimeline(conversationId: string): Promise<ToolCallTimelineItem[]>`

### Controller contracts (`frontend/src/lib/controllers`)

- `ChatController.startAgenticTurn(input: AgenticAskInput): AsyncIterable<AgentStreamEvent>`
- `ChatController.loadToolTimeline(input: { conversationId: string }): Promise<ToolCallTimelineItem[]>`

### Route contract map (locked)

- `/` `load()` returns:
  - `conversations: ConversationSummary[]`
  - `activeConversation: ConversationDetail | null`
  - `timeline: ToolCallTimelineItem[]`
  - `modelOptions: ModelOption[]`
  - `selectedModel: string`
- `/` chat action (or endpoint call) consumes `AgenticAskInput` and streams `AgentStreamEvent`.

## Plan

- [ ] **Step 1: Add domain contracts for agentic streaming**
      Add/update model interfaces listed in `## Interfaces and Models`.
      Verify: `pnpm --dir frontend check` passes.

- [ ] **Step 2: Implement chat service SSE parser for agentic events**
      Parse backend SSE frames into typed `AgentStreamEvent` values. Discard/ignore any payload-like
      fields not allowed in whitebox UI contracts.
      Verify: service unit tests cover all event kinds and malformed frames.

- [ ] **Step 3: Implement chat controller agentic orchestration**
      Add controller methods for starting a turn and fetching timeline data.
      Verify: controller tests pass with mocked service streams.

- [ ] **Step 4: Wire route loader/action contracts to new models**
      Update route server files and ensure returned shapes satisfy locked contracts.
      Verify: route type checks and smoke tests pass.

- [ ] **Step 5: Add/extend chat store for plan + timeline state**
      Track per-turn planner output, tool timeline, active filters, streaming content, and done state.
      Verify: store unit tests for state transitions (planner->tool->tokens->done).

- [ ] **Step 6: Add frontend integration scripts for agentic flow**
      Add `verify:agentic-e2e` script exercising stream parsing and event ordering.
      Verify: script passes against running backend.

- [ ] **Step 7: Final architecture audit**
      Ensure no service calls in components and no raw transport types leak outside services.
      Verify: all checks/tests pass.

## Tests

- `pnpm --dir frontend check`
- `pnpm --dir frontend test`
- `pnpm --dir frontend run verify:agentic-e2e`

Minimum required coverage:

- SSE parser for all `AgentStreamEvent` variants.
- Controller orchestration and timeline loading.
- Store transition sequence through one full agentic turn.

## Verification

1. Start backend + frontend.
2. `pnpm --dir frontend check`
3. `pnpm --dir frontend test`
4. `pnpm --dir frontend run verify:agentic-e2e`
5. Manual sanity on `/`: planner/filter and tool rows appear while answer streams.
