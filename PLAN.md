# Blueprint: TalkingCode V1 (Agentic RAG) — RECTIFIED

## Executor Instructions

1. **Read this file at the start of every loop.** This is the single source of truth.
2. **Execute only the next unchecked step.** Never skip ahead.
3. **Follow the referenced skill strictly** for each layer (python-swe, svelte-swe, svelte-ui).
4. **Verify before checking off.** Each step has explicit verification criteria.
5. **Commit after each completed step.** Format: `git add -A && git commit -m "blueprint: [step title]"`
6. **If blocked, add a blocker note** under the step explaining why, then stop.
7. **Never claim "partial" completion.** A step is either done and verified, or not done.

## Context

TalkingCode V1 is a BFF monorepo (SvelteKit frontend + FastAPI backend) for conversational code understanding over a user's GitHub repositories. The chat system is **agentic-first**: planner, tool-calling loop, structured metadata classification, and whitebox streaming UX.

The non-agentic retrieve -> generate path is **deprecated and removed**. All chat orchestration must follow the agent loop design.

## Current State Assessment

**What's actually working:**
- Backend scaffold exists (uv project, basic FastAPI app structure)
- Frontend scaffold exists (SvelteKit + shadcn-svelte initialized)
- Docker compose config exists

**What's missing (blocking gaps):**
- Backend domain dataclasses not implemented with proper slots/frozen
- ORM models incomplete (missing conversation_turns, tool_call_timeline)
- No repository layer implementations
- No services (planner, classifier, agent loop)
- No tool registry or tool implementations
- No SSE streaming infrastructure
- Frontend domain models missing
- No API client generation from OpenAPI
- No service/controller layer
- UI components not following design system
- No verification tests

**Policy:** Do not proceed past scaffolding until domain layer is solid. No shortcuts.

## Scope

**In scope:**
- Full-stack agentic RAG implementation
- Backend: planner + tool loop + classification + timeline persistence
- Frontend: architecture for agent stream events and timeline state
- Frontend UI: whitebox interaction design per DESIGN_SYSTEM.md
- End-to-end contract verification

**Out of scope:**
- Non-agentic chat orchestration (deprecated, removed)
- Tool payload rendering in UI (never show raw payloads)
- Confidence scoring subsystem
- Live GitHub fallback for file-details tool (cache-only)

## Architecture Decisions

- **Backend:** Strict `python-swe` patterns
  - Dataclass IO contracts: `@dataclass(slots=True, frozen=True)` for all service boundaries
  - Protocol interfaces + dataclass implementations
  - Repository pattern: ORM types never leave repository layer
  - Services never import each other; controllers orchestrate via TaskGroup
  - Factory per-request with session + user context

- **Planner & Tool Loop:**
  - Planner runs every turn with strict structured output
  - Retry policy: one retry on selected/default model, then fallback to `gemini-3-flash`
  - Loop limits: max 8 iterations, max 3 tools/turn
  - Tool contract enforcement: schemas from dataclass IO, unknown args rejected
  - Default tool execution: blocking (failure stops execution group)
  - Non-blocking calls only via explicit planner flag; failures recorded but don't abort
  - Tool timeout: 15 seconds default, per-tool overrides allowed

- **Streaming & Contracts:**
  - FastAPI SSE with named `event:` values and JSON `data:` payloads
  - Wire format: `snake_case` field names
  - Frontend maps to camelCase domain models only in service layer
  - Frontend rejects events with unknown payload fields (strict validation)
  - Whitebox stream shows tool names + visible args/filters only; payloads hidden

- **Frontend:** Strict `svelte-swe` patterns
  - openapi-fetch with types generated from backend OpenAPI spec
  - Service layer handles all API calls and mapping
  - Controllers orchestrate, routes stay thin
  - Stores hold reactive client state
  - No business logic in loaders/actions

- **UI:** Strict `svelte-ui` + `DESIGN_SYSTEM.md`
  - Design tokens in CSS custom properties
  - shadcn-svelte base components, themed via primitives
  - `svelte-ai-elements` for chat primitives
  - No default Tailwind palette leakage

- **Data Persistence:**
  - `conversation_turns` + `tool_call_timeline` tables with indexed turn ordering
  - Optional `tool_call_payload_cache` (encrypted, disabled by default, never exposed to frontend)

## Interfaces and Models

Detailed contracts in subplans:
- `backend-python-plan.md` — Backend dataclasses, protocols, persistence schema
- `frontend-svelte-plan.md` — Frontend domain models, service interfaces, event contracts
- `frontend-ui-plan.md` — UI component contracts, layout blueprint

Design system: `DESIGN_SYSTEM.md`

## Rectified Plan

### Phase 1: Backend Foundation (python-swe)

**All steps must follow `python-swe` skill patterns. Reference existing examples in the skill's reference files.**

- [ ] **Step 1.1: Implement domain dataclasses (slots=True, frozen=True)**
  Create `backend/src/talkingcode/models/` with:
  - `AgentTurnInput`, `PlannerInput`, `PlannerOutput`
  - `ToolGroupPlan`, `PlannedToolCall`, `StopRules`
  - `RetrievalFilters`, `Area` enum, `FileType` enum
  - `ToolExecutionRequest`, `ToolExecutionResult`
  - `WhiteboxEvent`, `WhiteboxEventKind` enum
  - `DocumentClassificationInput`, `DocumentClassificationOutput`
  - Tool IO: `RetrieveChunksToolInput/Output`, `GetFileDetailsToolInput/Output`
  
  Verify: All dataclasses have `slots=True, frozen=True`. Type-check passes.

- [ ] **Step 1.2: Implement error hierarchy**
  Create `backend/src/talkingcode/errors.py` with:
  - `AppError` (base)
  - `InputError`, `NotFoundError`, `InfraError`, `UnauthorisedError`
  
  Verify: No HTTP status codes in domain errors. Import test passes.

- [ ] **Step 1.3: Implement ORM models**
  Create `backend/src/talkingcode/repositories/orm/` with:
  - `base.py` — SQLAlchemy declarative base
  - Models per schema in `backend-python-plan.md`:
    - `Repository`, `Document`, `DocumentChunk`, `ChunkEmbedding`
    - `IngestionRun`, `ConversationTurn`, `ToolCallTimeline`
  
  Verify: All models have proper indexes. Alembic autogenerate produces valid migration.

- [ ] **Step 1.4: Implement repositories**
  Create `backend/src/talkingcode/repositories/`:
  - `conversation_repository.py` — CRUD for conversation turns + timeline
  - `document_repository.py` — Search by vector similarity, save documents/chunks
  - `timeline_repository.py` — Persist tool call timeline entries
  
  Follow repository pattern from `python-swe/references/sqlalchemy.md`.
  Verify: Repository methods return domain models (not ORM types). Unit tests pass.

- [ ] **Step 1.5: Implement document classifier service**
  Create `backend/src/talkingcode/services/document_classifier.py`:
  - Protocol `IDocumentClassifier`
  - Implementation with OpenAI structured outputs
  - Strict schema: `language`, `area`, `file_type`, `symbols`, `tags`
  
  Verify: Classification produces valid output for sample Python/JS files.

- [ ] **Step 1.6: Implement planner service**
  Create `backend/src/talkingcode/services/planner_service.py`:
  - Protocol `IPlannerService`
  - Implementation with OpenRouter integration
  - Strict structured output: `intent`, `filters`, `tool_groups`, `stop_rules`
  - Fallback policy: one retry, then `gemini-3-flash`
  
  Verify: Planner produces valid structured output. Fallback behavior tested.

- [ ] **Step 1.7: Implement tool registry**
  Create `backend/src/talkingcode/services/tool_registry.py`:
  - Protocol `IToolRegistry`
  - Register tools with dataclass IO schemas
  - `get_tool_definitions()` returns OpenRouter-compatible function definitions
  - Schema generation from dataclasses (no hand-written JSON)
  
  Verify: Tool schemas are valid and complete. Unknown arg rejection works.

- [ ] **Step 1.8: Implement tool executor with TaskGroup**
  Create `backend/src/talkingcode/services/tool_executor.py`:
  - Protocol `IToolExecutor`
  - `execute_group()` with `asyncio.TaskGroup` for parallel groups
  - Sequential execution for non-parallel groups
  - 3 tools/turn limit enforced
  - Blocking mode: failure stops group, subsequent groups skipped
  - Non-blocking mode: failures recorded, execution continues
  
  Tools to implement:
  - `run_retriever` — Vector similarity search with filters
  - `get_file_details_from_github` — Cache-only file details
  
  Verify: Parallel execution works. Timeout handling (15s default) works. Blocking/non-blocking behavior correct.

- [ ] **Step 1.9: Implement agent loop service**
  Create `backend/src/talkingcode/services/agent_loop_service.py`:
  - Protocol `IAgentLoopService`
  - `run_turn()` returns `AsyncGenerator[WhiteboxEvent, None]`
  - Planner every turn with intent + filters + tool_groups
  - Stop rules: max 8 iterations
  - Event emission: `planner_started`, `planner_ready`, `tool_call_started`, `tool_call_finished`, `assistant_token`, `assistant_done`, `agent_error`
  
  Verify: Stream events in correct order. Payload bodies never appear in events.

- [ ] **Step 1.10: Implement whitebox streaming + timeline persistence**
  Ensure `AgentLoopService`:
  - Creates timeline entries during execution
  - All WhiteboxEvent variants emitted correctly
  - Timeline persistence via TimelineRepository
  
  Verify: Timeline can be retrieved and replayed. Payload redaction verified.

- [ ] **Step 1.11: Implement controller**
  Create `backend/src/talkingcode/controllers/chat_controller.py`:
  - `ChatController` dataclass with injected services
  - `start_agentic_turn()` orchestrates agent loop
  - `get_timeline()` returns redacted timeline (no payloads)
  
  Verify: Controller follows TaskGroup orchestration pattern. No business logic in controller.

- [ ] **Step 1.12: Implement routes + SSE streaming**
  Create `backend/src/talkingcode/routes/chat_routes.py`:
  - `POST /chat/agentic` — SSE stream (application/x-ndjson is wrong, must be text/event-stream)
  - `GET /chat/timeline?conversation_id=<uuid>` — JSON response with redacted timeline
  
  FastAPI SSE with proper event framing: `event: <name>\ndata: <json>\n\n`
  
  Verify: OpenAPI spec generates correctly at `/openapi.json`. SSE format validated.

- [ ] **Step 1.13: Wire factory and dependencies**
  Update `backend/src/talkingcode/factory.py` and `dependencies.py`:
  - `AppFactory` assembles all services with proper DI
  - Request-scoped factory with session + user context
  - FastAPI dependencies for factory injection
  
  Verify: App starts. Health endpoint responds. Dependency injection works.

- [ ] **Step 1.14: Backend verification**
  Run full backend test suite:
  1. `alembic upgrade head`
  2. `pytest backend/tests/unit -q` — all pass
  3. `pytest backend/tests/integration -q` — all pass
  4. `ruff check backend/src backend/tests` — clean
  5. Start backend: `uvicorn talkingcode.app:app --reload`
  6. `curl -fsS http://localhost:8000/openapi.json -o /tmp/talkingcode-openapi.json`
  7. Confirm file is valid JSON and non-empty
  
  **Do not proceed to Phase 2 until all tests pass.**

### Phase 2: Frontend Architecture (svelte-swe)

**All steps must follow `svelte-swe` skill patterns.**

- [ ] **Step 2.1: Configure API client generation**
  Update `talkingcode-frontend/package.json`:
  - Add `generate:api` script that fetches from `http://localhost:8000/openapi.json`
  - Install `openapi-typescript` and `openapi-fetch`
  
  Verify: `pnpm run generate:api` produces valid `schema.d.ts`.

- [ ] **Step 2.2: Implement domain models**
  Create `talkingcode-frontend/src/lib/models/`:
  - `AgenticAskInput`, `AgentPlanView`, `RetrievalFilterView`
  - `ToolCallTimelineItem`, `Area`, `FileType`
  - `AgentStreamEvent` variants (planner_started, planner_ready, tool_call_started, tool_call_finished, assistant_token, assistant_done, agent_error)
  
  Verify: TypeScript strict mode passes.

- [ ] **Step 2.3: Implement service interfaces**
  Create `talkingcode-frontend/src/lib/services/IChatService.ts`:
  - `askAgentic(input): AsyncIterable<AgentStreamEvent>`
  - `getToolTimeline(conversationId): Promise<ToolCallTimelineItem[]>`
  
  Verify: Interfaces compile.

- [ ] **Step 2.4: Implement chat service with strict SSE parsing**
  Create `talkingcode-frontend/src/lib/services/ChatService.ts`:
  - openapi-fetch client setup
  - SSE parsing for named events
  - Strict validation: reject events with unknown payload fields
  - snake_case to camelCase mapping in mapper functions only
  - Timeline API integration
  
  Verify: Service handles all event types. Unknown fields cause parse errors (not silent ignore).

- [ ] **Step 2.5: Implement controller**
  Create `talkingcode-frontend/src/lib/controllers/ChatController.ts`:
  - `startAgenticTurn(input): AsyncIterable<AgentStreamEvent>`
  - `loadToolTimeline(input): Promise<ToolCallTimelineItem[]>`
  
  Verify: Controller delegates to service. No direct API calls.

- [ ] **Step 2.6: Implement API route for SSE streaming**
  Create `talkingcode-frontend/src/routes/api/chat/agentic/+server.ts`:
  - POST endpoint consuming `AgenticAskInput`
  - Streams `AgentStreamEvent` as SSE to frontend
  
  Verify: Route types are correct. Streaming works end-to-end.

- [ ] **Step 2.7: Implement store state machine**
  Create `talkingcode-frontend/src/lib/stores/chatStore.ts`:
  - Phases: idle -> planning -> tools -> streaming -> done/error
  - State: currentPlan, timeline, streamingContent, error
  
  Verify: Store transitions work correctly.

- [ ] **Step 2.8: Wire route loaders/actions**
  Update `talkingcode-frontend/src/routes/+page.server.ts`:
  - `load()` returns: activeConversation, timeline, selectedModel
  - Actions for non-streaming mutations
  
  Verify: Routes follow thin pattern. No business logic in routes.

- [ ] **Step 2.9: Frontend architecture verification**
  Run verification:
  1. `pnpm --dir talkingcode-frontend check` — passes
  2. `pnpm --dir talkingcode-frontend test` — passes (or no tests is OK for now)
  3. `pnpm --dir talkingcode-frontend run generate:api` — produces valid types
  
  **Do not proceed to Phase 3 until type-check passes.**

### Phase 3: Frontend UI (svelte-ui)

**All steps must follow `svelte-ui` skill + `DESIGN_SYSTEM.md`.**

- [ ] **Step 3.1: Apply design system tokens**
  Update `talkingcode-frontend/src/app.css` with full token set from DESIGN_SYSTEM.md:
  - Color tokens (primary, accent, neutrals, text, semantic)
  - Typography tokens (fonts, sizes, line-heights, letter-spacing)
  - Spacing tokens
  - Radius, shadow tokens
  
  Map to shadcn variables:
  ```css
  :root {
    --background: var(--color-surface);
    --foreground: var(--color-text);
    --primary: var(--color-primary);
    --accent: var(--color-accent);
    /* etc. */
  }
  ```
  
  Update `tailwind.config.js` to use CSS custom properties.
  
  Verify: No `bg-white`, `text-gray-*`, `text-blue-*` leakage in new code.

- [ ] **Step 3.2: Install svelte-ai-elements components**
  Run:
  ```bash
  pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/new-message.json
  pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/action.json
  ```
  
  Verify: Components render in a test page.

- [ ] **Step 3.3: Build primitive wrappers**
  Create `talkingcode-frontend/src/lib/components/primitives/`:
  - `Card.svelte` — themed wrapper with proper tokens
  - `Button.svelte` — themed button variants
  - `Badge.svelte` — themed badges for status
  - `Input.svelte` — themed input (if needed beyond shadcn)
  
  Verify: Primitives use CSS custom properties, not Tailwind defaults.

- [ ] **Step 3.4: Build domain UI components**
  Create `talkingcode-frontend/src/lib/components/domain/`:
  - `AgentPlanBanner.svelte` — shows intent + filters
  - `ToolTimeline.svelte` — list of tool calls
  - `ToolTimelineItem.svelte` — single tool call row
  - `FilterChips.svelte` — display active filters
  - `ChatMessage.svelte` — message display using svelte-ai-elements
  - `ChatMessageActions.svelte` — Retry/Copy/Show Filters actions
  
  Verify: All components use primitives. No raw HTML elements. Tool payloads never rendered.

- [ ] **Step 3.5: Implement chat page layout**
  Update `talkingcode-frontend/src/routes/+page.svelte`:
  - Header with TalkingCode branding
  - Chat canvas with sticky composer
  - Planner banner visibility
  - Tool timeline visibility
  - Message list with streaming support
  - Action row (Retry, Copy, Show Filters)
  
  Layout per `frontend-ui-plan.md`:
  - Desktop: nav 240px, conversation rail 320px, chat canvas flexible
  - Mobile: single column, rail in drawer
  
  Verify: Responsive behavior works. Composer sticky at bottom.

- [ ] **Step 3.6: UI verification**
  Run verification:
  1. `pnpm --dir talkingcode-frontend check` — passes
  2. `pnpm --dir talkingcode-frontend test` — passes
  3. Manual check: planner banner visible, timeline updates, filter chips show, streaming works, actions work
  4. Confirm: no tool payload data visible in UI

### Phase 4: Integration & Verification

- [ ] **Step 4.1: Docker compose verification**
  Run:
  ```bash
  docker compose config
  docker compose up --build -d
  ```
  
  Verify: All services start. Health checks pass.

- [ ] **Step 4.2: End-to-end agentic flow test**
  With backend + frontend running:
  1. Open frontend at `http://localhost:5173`
  2. Submit question: "What authentication patterns are used in this codebase?"
  3. Verify:
     - `planner_started` event appears
     - `planner_ready` shows intent + filters
     - Tool calls appear in timeline (names + visible args)
     - Tool call status updates (started -> finished/failed)
     - Assistant response streams token-by-token
     - No raw tool payloads visible
     - Actions (Retry, Copy, Show Filters) work
  
  **Capture screenshot or log output as evidence.**

- [ ] **Step 4.3: Final verification matrix**
  Run all commands in PLAN.md `## Verification` section:
  1. `docker compose config` ✓
  2. `docker compose up --build -d` ✓
  3. `curl -fsS http://localhost:8000/openapi.json -o /tmp/talkingcode-openapi.json` ✓
  4. `test -s /tmp/talkingcode-openapi.json` ✓
  5. `pytest backend/tests/unit -q` — all pass ✓
  6. `pytest backend/tests/integration -q` — all pass ✓
  7. `pnpm --dir talkingcode-frontend check` — passes ✓
  8. `pnpm --dir talkingcode-frontend test` — passes ✓
  9. End-to-end agentic flow works ✓

  **All must pass. No exceptions.**

## Subplan References

- `backend-python-plan.md` — Detailed backend contracts, persistence schema
- `frontend-svelte-plan.md` — Detailed frontend architecture contracts
- `frontend-ui-plan.md` — Detailed UI component contracts
- `DESIGN_SYSTEM.md` — Visual design tokens and conventions

## Tests

### Backend
- Unit tests: `pytest backend/tests/unit -q`
- Integration tests: `pytest backend/tests/integration -q`
- Lint: `ruff check backend/src backend/tests`

### Frontend
- Type check: `pnpm --dir talkingcode-frontend check`
- Unit tests: `pnpm --dir talkingcode-frontend test`
- API generation: `pnpm --dir talkingcode-frontend run generate:api`

### End-to-end
- Manual agentic flow verification (see Step 4.2)

## Verification

1. `docker compose config` — valid
2. `docker compose up --build -d` — services start
3. `curl -fsS http://localhost:8000/openapi.json -o /tmp/talkingcode-openapi.json` — succeeds
4. `test -s /tmp/talkingcode-openapi.json` — non-empty
5. `pytest backend/tests/unit -q` — all pass
6. `pytest backend/tests/integration -q` — all pass
7. `pnpm --dir talkingcode-frontend check` — passes
8. `pnpm --dir talkingcode-frontend test` — passes
9. Manual chat test:
   - Planner events appear
   - Tool names + visible args appear
   - Payloads hidden
   - Response streams correctly
   - Actions work
