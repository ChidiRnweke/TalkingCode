# Blueprint: Ingestion Access Control for Public App

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. **Read this file first.** Every loop, re-read this file before doing anything.
2. **Do the next unchecked step.** Find the first `- [ ]` item and do only that step.
3. **Verify before checking off.** Run the verification listed in the step.
4. **Commit after each step.** `git add -A && git commit -m "blueprint: [step title]"`
5. **Don't skip ahead.** Steps are ordered by dependency.
6. **Follow existing patterns.** Match structure used in referenced files.
7. **If stuck, document and move on.** Add a short blocker note under the step.
8. **Update this file.** Keep it as the single source of truth during execution.

## Context

TalkingCode is becoming publicly accessible, so ingestion triggers must not be callable by anonymous users. Chat endpoints remain public by design, but ingestion should become an operational/admin flow called by cron (or similar automation) using a secret from `.env`.

Current backend routing separates chat and repo concerns (`backend/src/talkingcode/routes/chat_routes.py`, `backend/src/talkingcode/routes/repo_routes.py`). Ingestion triggers currently sit in repo routes and can be invoked without auth. Config is centralized in `backend/src/talkingcode/config.py` and injected via FastAPI dependencies in `backend/src/talkingcode/dependencies.py`, making a route-level API key dependency the lowest-risk integration point.

Frontend already has a repos page that reads tracked repos via `GET /api/repos` and displays ingestion metadata (`talkingcode-frontend/src/routes/repos/+page.server.ts`, `talkingcode-frontend/src/lib/components/domain/RepoCard.svelte`). That visibility should stay. The write actions (ingest/register) should be removed or disabled in public UI so users can view repository ingestion state without being able to trigger ingestion.

## Scope

**In scope:**

- Protect ingestion-related write endpoints with an env-configured API key.
- Keep chat endpoints public.
- Keep repo visibility endpoints available for UI read access.
- Update frontend repos page/cards to read-only ingestion visibility (no public trigger buttons).
- Add/adjust tests for auth gate and public read/chat behavior.
- Document cron usage for protected ingestion endpoint(s).

**Out of scope:**

- User accounts, OAuth, JWT, or role-based access control.
- Re-architecting ingestion pipeline internals.
- New scheduler infrastructure implementation.
- Changes to chat model access policy.

## Architecture Decisions

- Use a **shared FastAPI dependency** for ingestion auth in `backend/src/talkingcode/dependencies.py`, consistent with existing dependency injection patterns (`FactoryDep`, `ConfigDep`).
- Add `INGESTION_API_KEY` to `Settings`/`AppConfig` in `backend/src/talkingcode/config.py` and fail auth when missing/invalid key is supplied.
- Apply auth dependency only to **repo write routes** that trigger ingestion state changes:
  - `POST /repos`
  - `POST /repos/{owner}/{name}/ingest`
  - `POST /repos/ingest-owned`
- Keep read routes public so frontend can continue rendering repo status:
  - `GET /repos`
  - `GET /repos/{owner}/{name}`
  - `GET /repos/{owner}/{name}/runs`
- Accept both `X-API-Key` header and `api_key` query param for cron friendliness.
- Prefer raising `HTTPException(status_code=401)` in dependency for precise HTTP semantics and minimal global error-handler changes.

## Interfaces and Models

- Config additions:
  - `Settings.ingestion_api_key: str = ""`
  - `AppConfig.ingestion_api_key: str`
  - Pass through in `AppConfig.from_env()`
- New dependency in `backend/src/talkingcode/dependencies.py`:
  - `require_ingestion_api_key(config: ConfigDep, x_api_key: Header | None, api_key: Query | None) -> None`
  - Effective key = `x_api_key or api_key`
  - Reject when key is absent/invalid.
- Route integration:
  - Add dependency to protected repo write endpoints in `backend/src/talkingcode/routes/repo_routes.py`.
- Frontend behavior contract:
  - Repos page continues to call read endpoints.
  - Public UI no longer exposes ingestion trigger action.

## Plan

- [ ] **Step 1: Add ingestion API key config and auth dependency**
      Update `backend/src/talkingcode/config.py` with `ingestion_api_key` in both `Settings` and `AppConfig`, including `from_env()` wiring. Add `require_ingestion_api_key` in `backend/src/talkingcode/dependencies.py` following existing dependency style in the same file. Use FastAPI header/query extraction and return `401` on missing/invalid key. Verify by importing app modules and running unit tests.

- [ ] **Step 2: Protect repo write endpoints and keep read/chat public**
      In `backend/src/talkingcode/routes/repo_routes.py`, attach the new dependency to `POST /repos`, `POST /repos/{owner}/{name}/ingest`, and `POST /repos/ingest-owned`. Do not attach it to any GET routes. Confirm `backend/src/talkingcode/routes/chat_routes.py` remains unchanged/public. Verify with API tests or manual curl checks for 401 vs 200 behavior.

- [ ] **Step 3: Make repos UI read-only for ingestion actions**
      Update `talkingcode-frontend/src/routes/repos/+page.svelte` and `talkingcode-frontend/src/lib/components/domain/RepoCard.svelte` to remove/disable public ingestion trigger controls while preserving repo list, `last_ingested_at`, and run history visibility. Keep design conventions from `DESIGN_SYSTEM.md` and existing component styling patterns. Verify page renders and loads repo data without attempting protected POST calls.

- [ ] **Step 4: Add tests for access policy and document cron usage**
      Add/update backend tests to cover: (a) protected repo write endpoints require key, (b) key works for authorized calls, (c) repo read and chat endpoints stay public. Add a short ops doc (README or backend docs) showing cron-safe calls using `X-API-Key` and/or query param to `POST /repos/ingest-owned`. Verify test suite pass and commands are copy-pastable.

## Tests

- Backend tests to add/update:
  - unauthorized request to protected POST route returns `401`
  - authorized request with `X-API-Key` succeeds (or reaches business logic)
  - authorized request with `api_key` query succeeds
  - `GET /repos` remains accessible without key
  - `POST /chat/agentic` remains accessible without key (or route-level test if full integration is heavy)
- Frontend verification:
  - repos page still renders repo cards and ingestion history controls
  - no public ingest POST is triggered from UI interactions
- Suggested commands:
  - `cd backend && uv run pytest`
  - `cd talkingcode-frontend && pnpm test` (if configured)
  - `cd talkingcode-frontend && pnpm check` (or existing project validation command)

## Verification

- Set `.env` with `INGESTION_API_KEY=your-secret`.
- Start backend and frontend.
- Confirm without key:
  - `GET /repos` returns data.
  - `GET /repos/{owner}/{name}/runs` returns data (if repo exists).
  - `POST /chat/agentic` works.
  - Protected POST repo routes return `401`.
- Confirm with key:
  - `curl -X POST "http://localhost:8000/repos/ingest-owned" -H "X-API-Key: your-secret"`
  - (optional cron-friendly query form) `curl -X POST "http://localhost:8000/repos/ingest-owned?api_key=your-secret"`
- Open UI `/repos` and verify ingested repositories are visible while ingestion is not triggerable by anonymous users.
