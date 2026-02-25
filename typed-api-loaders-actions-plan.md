# Blueprint: Remove Frontend Repo API Proxies, Adopt Typed OpenAPI Server Flow

## Executor Instructions

1. Re-read this file at the start of every loop.
2. Execute the next unchecked step only.
3. Verify before checking off each step.
4. Commit after each completed step with `blueprint: <step title>`.
5. Do not reintroduce non-chat routes under `talkingcode-frontend/src/routes/api/`.
6. For non-chat data, do not use raw `fetch()` from browser code.
7. Keep chat behavior intact; chat route may remain.

## Non-Negotiable Requirement

After refactor, frontend API routes are chat-only.

- Keep: `talkingcode-frontend/src/routes/api/chat/agentic/+server.ts`
- Delete: all `talkingcode-frontend/src/routes/api/repos/**`
- Ensure zero fallback aliases and zero compatibility proxies for repos.

## Context

Current state is mixed and violates the desired pattern:

- Repo list is server loaded (`talkingcode-frontend/src/routes/repos/+page.server.ts`).
- Repo history is still fetched in browser (`talkingcode-frontend/src/lib/components/domain/RepoCard.svelte` via `RepoService`).
- Repo proxy handlers exist under `talkingcode-frontend/src/routes/api/repos/**`.
- `openapi-typescript` and `openapi-fetch` are installed, but generated schema file is missing from source tree.

Desired state:

- Non-chat: server `load`/`actions` only, through typed OpenAPI wrappers.
- Chat: exception, keep existing behavior.

## Scope

**In scope:**

- Backend API schema model centralization in `backend/src/talkingcode/models/`.
- OpenAPI quality improvements needed for type generation.
- Frontend OpenAPI type generation and typed client factory.
- Service-boundary mapping from raw API types to frontend domain/view models.
- Repo page full server preprocess: preload repos and all runs, stream response to UI.
- Removal of all frontend repo proxy routes and browser repo service calls.

**Out of scope:**

- Backend endpoint deletion in this pass.
- Chat SSE protocol redesign.
- Any UI redesign.

## OpenAPI Rules (from svelte-swe reference)

These are mandatory:

1. Never instantiate API clients outside a dedicated factory.
2. Never use raw OpenAPI schema component types outside service files.
3. Never use raw `fetch()` for non-chat API calls.
4. Always map raw API DTOs to domain/view models at service boundary.
5. Always handle `{ data, error }` from every openapi-fetch call.
6. Regenerate `schema.d.ts` when backend OpenAPI changes.

## Architecture Decisions

1. **Frontend API policy**
   - `src/routes/api/` becomes chat-only.
   - Repos flow lives in server loaders/actions and server-side API modules.

2. **Data loading policy**
   - Repos page load preloads:
     - all repos
     - all run histories for each repo
   - Streaming is used so page renders list while histories resolve.

3. **Typed transport policy**
   - Source of truth: generated OpenAPI file `talkingcode-frontend/src/lib/api/schema.d.ts`.
   - Service files map raw API models to app-level models before returning to routes/components.

4. **Auth policy**
   - Implement ingestion auth through openapi-fetch middleware, not ad hoc per-request code.

## File and Module Design

### Backend: API schema models

Create one or more API schema modules under `backend/src/talkingcode/models/` (for example `api.py`).

Move route-local models from route files into shared API schema modules:

- `RegisterRepoRequest`
- `StartIngestionRequest`
- `ModelInfoResponse`
- `ModelListResponse`
- `ToolCallInfoResponse`
- `ToolTimelineResponse`
- `ChatAgenticRequest` (typed request payload for `/chat/agentic`)

Keep ORM in `backend/src/talkingcode/models/orm.py` unchanged.

### Frontend: typed OpenAPI stack

Create/ensure these files:

- `talkingcode-frontend/src/lib/api/schema.d.ts` (generated)
- `talkingcode-frontend/src/lib/server/api/client.ts` (factory + middleware)
- `talkingcode-frontend/src/lib/server/api/repos.service.ts` (service + mapping)
- `talkingcode-frontend/src/lib/server/api/models.service.ts` (service + mapping)

If needed for clean model mapping:

- `talkingcode-frontend/src/lib/server/api/mappers/repos.ts`
- `talkingcode-frontend/src/lib/server/api/mappers/models.ts`

## Plan

- [x] **Step 1: Confirm deletion surface and current call graph**
      Identify every call path that currently depends on repo proxy routes.

      Confirm these files are deletion targets:
      - `talkingcode-frontend/src/routes/api/repos/+server.ts`
      - `talkingcode-frontend/src/routes/api/repos/[owner]/[name]/+server.ts`
      - `talkingcode-frontend/src/routes/api/repos/[owner]/[name]/ingest/+server.ts`
      - `talkingcode-frontend/src/routes/api/repos/[owner]/[name]/runs/+server.ts`
      - `talkingcode-frontend/src/routes/api/repos/ingest-owned/+server.ts`

      Confirm chat keep target:
      - `talkingcode-frontend/src/routes/api/chat/agentic/+server.ts`

      Verify:
      - Every `/api/repos` string usage is listed.
      - Every `RepoService` usage is listed.

      Execution notes:
      - `/api/repos` usage found only in `talkingcode-frontend/src/lib/services/RepoService.ts` (6 call sites).
      - `RepoService` usage found in `talkingcode-frontend/src/lib/components/domain/RepoCard.svelte` and service-layer files.
      - Deletion targets and chat keep target paths exist exactly as listed.

- [x] **Step 2: Centralize backend API request/response models under models package**
      Move route-local API schemas from:
      - `backend/src/talkingcode/routes/repo_routes.py`
      - `backend/src/talkingcode/routes/model_routes.py`
      - `backend/src/talkingcode/routes/chat_routes.py`

      Into shared API schema module(s) in `backend/src/talkingcode/models/`.

      Ensure route function signatures explicitly reference these models so OpenAPI emits concrete schemas.

      Execution notes:
      - Added shared schema module `backend/src/talkingcode/models/api.py`.
      - Routes now import `RegisterRepoRequest`, `StartIngestionRequest`, `ModelInfoResponse`, `ModelListResponse`, `ChatAgenticRequest`, `ToolCallInfoResponse`, and `ToolTimelineResponse` from shared models.
      - Removed route-local schema class definitions in repo/model/chat route modules.


- [x] **Step 3: Add/normalize OpenAPI generation workflow in frontend**
      Ensure generation script is authoritative and deterministic:
      - script should produce `src/lib/api/schema.d.ts`
      - document that schema regeneration is required after backend schema changes

      Run generation and commit produced file.

      Verify:
      - `talkingcode-frontend/src/lib/api/schema.d.ts` exists
      - file includes `paths` and `components` types for repo/model/chat routes

      Execution notes:
      - Added deterministic export script `talkingcode-frontend/scripts/export-openapi.py` (builds OpenAPI directly from backend app factory).
      - Updated frontend scripts: `export:openapi` and `generate:api` now regenerate `openapi.json` and `src/lib/api/schema.d.ts`.
      - Documented regeneration rule in `talkingcode-frontend/README.md`.

- [x] **Step 4: Implement typed client factory with middleware auth**
      Create `talkingcode-frontend/src/lib/server/api/client.ts`:
      - instantiate `openapi-fetch` once via factory
      - use env base URL
      - install middleware for auth injection on ingestion-protected endpoints

      Middleware behavior:
      - apply `X-API-Key` header (or query) only when needed
      - avoid leaking auth into unrelated endpoints

      Verify:
      - service modules consume `ApiClient` type from factory only
      - no direct client instantiation outside factory

      Execution notes:
      - Added `talkingcode-frontend/src/lib/server/api/client.ts` with `createApiClient()` and exported `ApiClient` type.
      - Added middleware that injects `X-API-Key` only for POST ingestion-protected schema paths (`/repos`, `/repos/ingest-owned`, `/repos/{owner}/{name}/ingest`).
      - Verified `openapi-fetch` client instantiation exists only in the factory module.

- [x] **Step 5: Create typed repo/model service modules with explicit DTO mapping**
      Add service modules that:
      - call typed endpoints via client
      - handle `{ data, error }` from each request
      - map raw API schemas to app-level return shapes

      Minimum methods:
      - repos: list repos, list ingestion runs, start ingestion, start owned ingestion
      - models: list models

      Verify:
      - route server files can consume service methods without importing raw `components['schemas']` types

      Execution notes:
      - Added `talkingcode-frontend/src/lib/server/api/repos.service.ts` and `talkingcode-frontend/src/lib/server/api/models.service.ts` using `ApiClient` from the factory.
      - Added explicit mappers at `talkingcode-frontend/src/lib/server/api/mappers/repos.ts` and `talkingcode-frontend/src/lib/server/api/mappers/models.ts`.
      - Implemented explicit `{ data, error }` handling for every typed request and validated TypeScript via `pnpm run check`.

- [x] **Step 6: Refactor repos server load to preload all runs and stream**
      Update `talkingcode-frontend/src/routes/repos/+page.server.ts`:
      - call repo service to load repos
      - preload all ingestion runs for each repo server-side
      - return streaming-friendly payload so base UI renders quickly

      Verify:
      - repos list renders immediately
      - histories populate without client-side API calls
      - no usage of `/api/repos` endpoints

      Execution notes:
      - Replaced legacy server repo service usage with typed `createReposService(fetch)` in `talkingcode-frontend/src/routes/repos/+page.server.ts`.
      - Added server-side preload of all per-repo ingestion histories as promise values in `runsByRepo` for streaming-friendly resolution.
      - Verified no `/api/repos` usage in repos page server load and validated with `pnpm run check`.

- [x] **Step 7: Convert RepoCard to pure presentation component**
      Update `talkingcode-frontend/src/lib/components/domain/RepoCard.svelte`:
      - remove `RepoService` import
      - remove async network logic
      - accept preloaded history data by props
      - keep local show/hide UI state only

      Verify:
      - history toggle works with preloaded data
      - no browser network for repo history

      Execution notes:
      - Refactored `talkingcode-frontend/src/lib/components/domain/RepoCard.svelte` to remove all service imports and network calls.
      - `RepoCard` now accepts `historyRuns` as a prop and uses local show/hide UI state only.
      - Wired `talkingcode-frontend/src/routes/repos/+page.svelte` to pass preloaded per-repo history promises from server load; validated with `pnpm run check`.

- [x] **Step 8: Remove obsolete repo proxy routes and unused repo services**
      Delete all repo routes under `talkingcode-frontend/src/routes/api/repos/**`.

      Remove unused modules after rewiring:
      - `talkingcode-frontend/src/lib/services/RepoService.ts`
      - `talkingcode-frontend/src/lib/services/IRepoService.ts` (if unused)
      - `talkingcode-frontend/src/lib/services/RepoServiceServer.ts` (if replaced)

      Verify:
      - `src/routes/api/` contains chat route only
      - global search returns zero `/api/repos` references

      Execution notes:
      - Deleted all frontend repo proxy route handlers under `talkingcode-frontend/src/routes/api/repos/**`.
      - Removed obsolete repo service modules: `RepoService.ts`, `IRepoService.ts`, and `RepoServiceServer.ts`.
      - Verified `src/routes/api/` now contains only `talkingcode-frontend/src/routes/api/chat/agentic/+server.ts` and confirmed zero endpoint-string references to `/api/repos`.

- [ ] **Step 9: Align frontend models with generated transport + mapped domain models**
      Update `talkingcode-frontend/src/lib/models/index.ts` to avoid duplicate transport DTOs.

      Rule:
      - API transport shapes stay in generated schema and service internals.
      - UI components consume app/domain models returned by services/loaders.

      Verify:
      - no duplicate repo/model transport interfaces conflicting with generated schema

- [ ] **Step 10: Validate chat exception and keep it isolated**
      Confirm chat still works and remains the only route under `src/routes/api/`.

      Optional hardening:
      - if chat service currently calls backend directly, decide whether to keep direct call or route through chat proxy, but do not expand this to repos.

      Verify:
      - `/chat` SSE flow unchanged
      - non-chat does not use raw client fetch

- [ ] **Step 11: Test and finalize docs**
      Run checks:
      - frontend: `pnpm run check && pnpm run test:unit && pnpm run build`
      - backend: `pytest`

      Update docs with:
      - chat-only frontend API route policy
      - openapi generation command and regeneration rule
      - service boundary mapping rule
      - no-raw-fetch rule for non-chat

      Verify:
      - manual smoke: `/repos`, repo history display, `/chat`

## Verification Checklist

- [ ] Frontend `src/routes/api/` contains only chat route.
- [ ] All repo proxy routes are deleted.
- [ ] Zero `/api/repos` references remain in frontend.
- [ ] `RepoCard` contains no network logic.
- [ ] Repos and histories are loaded server-side and streamed.
- [ ] `schema.d.ts` exists and is committed.
- [ ] Typed client factory exists with auth middleware.
- [ ] Services map raw OpenAPI DTOs to app-level models.
- [ ] Non-chat paths contain no browser raw `fetch()` to backend/proxy.
- [ ] Chat behavior remains unchanged.

## Command Checklist

- Generate API types:
  - `cd talkingcode-frontend && pnpm run generate:api`
- Frontend quality gate:
  - `cd talkingcode-frontend && pnpm run check && pnpm run test:unit && pnpm run build`
- Backend quality gate:
  - `cd backend && pytest`

## Notes

- This blueprint intentionally does not delete backend routes; it only removes frontend repo proxies and rewires frontend architecture.
- If backend route reduction is desired later, do a separate audited blueprint so cron/automation integrations are not broken unexpectedly.
