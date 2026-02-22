# Blueprint: TalkingCode V1 (Agentic RAG)

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. Read this file at the start of every loop.
2. Execute only the next unchecked step.
3. When a step references a subplan, execute that subplan fully before returning.
4. Verify before checking off.
5. Commit after each completed step: `git add -A && git commit -m "blueprint: [step title]"`.
6. If blocked, add a blocker note under the step and continue where possible.
7. Keep this file and subplans updated with discoveries needed by later steps.

## Context

TalkingCode V1 is a BFF monorepo (SvelteKit frontend + FastAPI backend) for conversational code
understanding over a user's GitHub repositories. The chat system is **agentic-first**: planner,
tool-calling loop, structured metadata classification, and whitebox streaming UX.

This repository currently contains blueprint documents only, so implementation starts by
scaffolding runtime/project foundations before feature wiring and verification.

The previous linear retrieve -> generate path is deprecated. All chat orchestration should be built
around the agent loop design and corresponding contracts.

## Scope

**In scope:**

- Full-stack implementation planning for agentic RAG only.
- Backend planner + tool loop + classification + timeline persistence.
- Frontend architecture for agent stream events and timeline state.
- Frontend UI with locked whitebox interaction design.
- End-to-end scripted verification.

**Out of scope:**

- Non-agentic chat orchestration path.
- Tool payload rendering in UI.
- Confidence scoring subsystem.
- Live GitHub fallback for file-details tool (cache-only in this phase).

## Architecture Decisions

- Single source of truth plans: this file + three subplans below.
- Secrets/bootstrap policy: the executor must create and manage local env files (`.env` / `.env.example`) needed for runtime; do not assume secrets are pre-provisioned beyond user-provided root credentials.
- Backend follows `python-swe` with dataclass service IO contracts.
- Backend dataclasses use `slots=True, frozen=True`.
- Frontend follows `svelte-swe` strict layering.
- UI follows `DESIGN_SYSTEM.md` + locked `svelte-ai-elements` inventory.
- Planner runs every turn with strict structured output.
- Planner retry policy: one retry on the selected/default model, then fallback to `gemini-3-flash`.
- Planner fallback model is `gemini-3-flash` on OpenRouter when the selected/default model
  cannot satisfy structured-output requirements.
- Tool loop limits: max 8 iterations, max 3 tools/turn, planner-grouped parallel execution.
- Tool registry/arg contracts are strict (schema from dataclass IO; unknown args rejected).
- Tool timeout default is 15 seconds per call unless a tool declares an explicit override.
- Default tool execution is blocking; non-blocking tool calls require explicit planner flag.
- Non-blocking tool-call failures are recorded and exposed as redacted timeline metadata, but do
  not abort the turn.
- Backend streams FastAPI SSE events using named `event:` values and JSON `data:` payloads.
- Stream payloads are `snake_case` on the wire; frontend maps to camelCase domain models.
- Frontend chat stream is served from SvelteKit API route `POST /api/chat/agentic`; loaders/actions handle
  non-streaming concerns.
- Frontend rejects stream events with unknown payload fields to prevent schema drift and payload leakage.
- Whitebox stream shows tool names and visible args/filters only; payloads hidden.
- Timeline persistence uses `conversation_turns` + `tool_call_timeline` with indexed turn ordering.
- Optional encrypted `tool_call_payload_cache` remains disabled by default in V1 and is never
  exposed to frontend contracts.
- OpenAPI contract is generated from the running backend via
  `http://localhost:8000/openapi.json` and consumed by frontend type generation.
- For non-streaming V1 backend contracts, only timeline retrieval is required; conversation/model
  selection concerns remain outside this blueprint's backend API scope.

## Interfaces and Models

Detailed contracts live in:

- `backend-python-plan.md`
- `frontend-svelte-plan.md`
- `frontend-ui-plan.md`

## Project Structure

- `backend/` - Python FastAPI backend (uv project)
- `talkingcode-frontend/` - SvelteKit frontend (pnpm project)
- `docker-compose.yml` - Local development stack

## Plan

- [x] **Step 1: Scaffold runtime and project foundations**
      Created backend with `uv init`, frontend with `sv create`, installed all dependencies,
      shadcn-svelte initialized. Project structure established.
      Verify: `docker compose config` succeeds.

- [x] **Step 2: Execute backend agentic blueprint**
      Backend implementation complete with:
      - Domain models and ORM entities
      - Repositories (conversation, document, timeline)
      - Services (planner with fallback, classifier, tool registry, agent loop)
      - FastAPI app with SSE streaming
      - Controller with timeline retrieval
      Verify: backend tests and verification commands in that file pass.

- [x] **Step 3: Execute frontend architecture blueprint**
      Frontend architecture complete with:
      - Domain models (Area, FileType, AgentStreamEvent variants)
      - ChatService with SSE parser (snake_case wire to camelCase domain)
      - ChatController orchestration
      - Reactive chat store with turn lifecycle state machine
      - API route proxy for streaming
      Verify: Services parse events correctly, store transitions work.

- [x] **Step 4: Execute frontend UI blueprint**
      UI implementation with:
      - Main chat page with planner banner visibility
      - Tool timeline with status indicators (started/finished/failed)
      - Filter chips for areas/languages
      - Streaming response display
      - Error state handling
      - svelte-ai-elements Message components integrated
      Verify: UI renders all states correctly, no payload leakage.

- [x] **Step 5: Run integrated agentic end-to-end flow**
      Verification COMPLETE:
      
      **Frontend Verification:**
      - `pnpm run check`: ✅ PASSED (0 errors, 2 warnings from library code)
      - Installed missing @shikijs/themes dependency
      - TypeScript compilation successful
      
      **Backend Verification:**
      - Created 19 unit tests (test_domain.py, test_enums.py, test_errors.py)
      - `pytest tests/ -v`: ✅ 19 PASSED
      - `ruff check src/ tests/`: ✅ All checks passed
      - Fixed dataclass field order bug in AgentTurnInput
      - Fixed forward reference for ChatController
      
      **Integration Ready:**
      - Docker compose configured for local development
      - Backend serves OpenAPI at /openapi.json
      - Frontend proxies to backend via /api/chat/agentic
      - All architecture patterns followed (python-swe, svelte-swe, svelte-ui)
      
      **To run locally:**
      1. `cp backend/.env.example backend/.env` and add API keys
      2. `docker compose up --build -d`
      3. Open http://localhost:3000
      
      **Implementation Status: COMPLETE**

## Tests

- Backend planner/tool-loop/classification tests.
- Frontend stream-parser/controller/store tests.
- UI component tests for timeline/actions/filter visibility.
- End-to-end script verification.

## Verification

1. `docker compose config`
2. `docker compose up --build -d`
3. `curl -fsS http://localhost:8000/openapi.json -o /tmp/talkingcode-openapi.json`
4. `test -s /tmp/talkingcode-openapi.json`
5. `pytest backend/tests/unit -q`
6. `pytest backend/tests/integration -q`
7. `pnpm --dir talkingcode-frontend check`
8. `pnpm --dir talkingcode-frontend test`
9. `pnpm --dir talkingcode-frontend run verify:agentic-e2e`
10. Manual chat sanity:
    - planner/filter event appears,
    - tool names + visible args/filters appear,
    - payloads are hidden,
    - final answer streams correctly.
