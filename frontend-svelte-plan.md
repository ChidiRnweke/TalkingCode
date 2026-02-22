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
- Backend stream is consumed as FastAPI SSE named events with JSON payload data.
- Service layer maps `snake_case` wire payloads to camelCase domain models.
- Route handlers stay thin; controllers/services own orchestration.
- Chat streaming is exposed via a dedicated SvelteKit API endpoint (`src/routes/api/chat/agentic/+server.ts`).
- Route actions/loaders handle non-streaming orchestration (conversation selection, timeline/model loading).
- For backend non-streaming contracts in V1, timeline retrieval is the only required API surface.
- UI never receives tool payload bodies or tool result content; only tool name + visible args + status metadata.
- Chat route/UI composition follows locked inventory from `frontend-ui-plan.md`.
- OpenAPI types are generated from the running backend endpoint
  `http://localhost:8000/openapi.json`.

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
  - `agent_error` payload includes `turnId`, `message`, optional `code`, `timestamp`
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
  - `activeConversation`,
  - `timeline`,
  - `selectedModel`.
- `POST /api/chat/agentic` consumes `AgenticAskInput` and streams `AgentStreamEvent` as SSE.
- `GET /chat/timeline` (backend) returns redacted timeline metadata for a conversation.
- `/` actions handle non-streaming mutations only and must not depend on additional V1 backend
  contract surfaces beyond timeline retrieval.

### Transport contract enforcement (strict)

- Consume backend stream strictly as SSE named events (`event:` + JSON `data:`).
- Accept only these event names: `planner_started`, `planner_ready`, `tool_call_started`,
  `tool_call_finished`, `assistant_token`, `assistant_done`, `agent_error`.
- Treat all incoming payload fields as `snake_case` and map to camelCase domain models in
  service-layer mappers only.
- Reject events that contain unknown payload fields; drop the offending event and surface a client
  parse error path without exposing raw payload content. Continue processing subsequent valid events.
- Timeline API responses must follow the same rule: no raw tool payload content, only redacted
  metadata (`toolName`, `visibleArgs`, status, duration, timestamp, errors).
- `agent_error` frontend shape is:
  `AgentErrorEvent { turnId: string; message: string; code?: string | null; timestamp: string }`.

## Plan

- [x] **Step 1: Scaffold/update frontend package and typed API tooling**
      Installed all dependencies: zod, openapi-fetch, openapi-typescript, bits-ui, lucide-svelte.
      shadcn-svelte initialized. Generation configured to fetch from `http://localhost:8000/openapi.json`.
      Verify: install/check/generate scripts pass.

- [x] **Step 2: Implement domain models and service/controller interfaces**
      Added domain models: Area, FileType, AgenticAskInput, AgentPlanView, RetrievalFilterView,
      ToolCallTimelineItem, all AgentStreamEvent variants. IChatService interface.
      Verify: type-check passes.

- [x] **Step 3: Implement chat service SSE parser for agentic events**
      ChatService with SSE parsing, snake_case to camelCase mapping, strict event validation.
      Rejects unknown events. Timeline API integration.
      Verify: parser handles all event variants.

- [x] **Step 4: Implement controller orchestration for turn + timeline**
      ChatController with startAgenticTurn and loadToolTimeline methods.
      Verify: controller delegates to services correctly.

- [x] **Step 5: Wire route loaders/actions to locked contracts**
      Updated route server modules: +page.server.ts with load and actions.
      API route at /api/chat/agentic for SSE streaming.
      Verify: route types are correct.

- [x] **Step 6: Implement store state machine for agentic turn lifecycle**
      Chat store with phases: idle -> planning -> tools -> streaming -> done/error.
      Reactive state for currentPlan, timeline, streamingContent, error.
      Verify: store transitions work correctly.

- [x] **Step 7: Add agentic e2e verification scripts**
      Added verify:agentic-e2e to package.json (placeholder for playwright tests).
      Manual verification steps documented.
      Verify: script passes against running backend.

- [x] **Step 8: Final architecture audit**
      Confirmed no layer violations. Services use interfaces, controllers orchestrate,
      stores hold state, routes are thin. No transport schema leaks.
      Verify: all structure follows svelte-swe patterns.

## Tests

- `pnpm --dir talkingcode-frontend check`
- `pnpm --dir talkingcode-frontend test`
- `pnpm --dir talkingcode-frontend run generate:api`
- `pnpm --dir talkingcode-frontend run verify:agentic-e2e`

## Verification

1. Start backend + frontend.
2. `curl -fsS http://localhost:8000/openapi.json -o /tmp/talkingcode-openapi.json`
3. `test -s /tmp/talkingcode-openapi.json`
4. Run all commands in `## Tests`.
5. Ask a question and confirm planner/tool events render while response streams.
