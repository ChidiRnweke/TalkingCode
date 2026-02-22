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

- [x] **Step 1: Add env setting field in `Settings`**
      File: `backend/src/talkingcode/config.py`.
      Add `ingestion_api_key: str = ""` under existing API key settings in `Settings`.
      Do not remove existing fields.
      **Verify:** run `cd backend && uv run python -c "from talkingcode.config import Settings; print(hasattr(Settings(), 'ingestion_api_key'))"` and confirm output is `True`.

- [x] **Step 2: Add runtime config field in `AppConfig`**
      File: `backend/src/talkingcode/config.py`.
      Add `ingestion_api_key: str` to the `AppConfig` dataclass.
      Keep dataclass frozen/slots exactly as-is.
      **Verify:** run `cd backend && uv run python -c "from talkingcode.config import AppConfig; print('ingestion_api_key' in AppConfig.__annotations__)"` and confirm output is `True`.

- [x] **Step 3: Wire setting into `AppConfig.from_env()`**
      File: `backend/src/talkingcode/config.py`.
      In `from_env()`, pass `settings.ingestion_api_key` into `AppConfig(...)`.
      Keep argument order consistent with nearby fields.
      **Verify:** run `cd backend && uv run python -c "from talkingcode.config import AppConfig; c=AppConfig.from_env(); print(hasattr(c,'ingestion_api_key'))"` and confirm output is `True`.

- [x] **Step 4: Add ingestion auth dependency function**
      File: `backend/src/talkingcode/dependencies.py`.
      Add a new dependency function named `require_ingestion_api_key`.
      Inputs:
      - `config: ConfigDep`
      - `x_api_key` from request header `X-API-Key`
      - `api_key` from query param `api_key`
      Behavior:
      - choose effective key as header first, else query
      - if no configured key in env, reject with `HTTPException(status_code=401)`
      - if provided key mismatches configured key, reject with `HTTPException(status_code=401)`
      - on success return `None`
      **Verify:** run `cd backend && uv run python -m compileall src` and ensure no syntax errors.

- [x] **Step 5: Export dependency alias for clean route signatures**
      File: `backend/src/talkingcode/dependencies.py`.
      Add a typed alias similar to `FactoryDep`, e.g. `IngestionAuthDep = Annotated[None, Depends(require_ingestion_api_key)]`.
      **Verify:** run `cd backend && uv run python -c "from talkingcode.dependencies import IngestionAuthDep; print(IngestionAuthDep is not None)"`.

- [x] **Step 6: Protect `POST /repos`**
      File: `backend/src/talkingcode/routes/repo_routes.py`.
      Import the new auth dependency alias and add it to `register_repo(...)` route parameters (unused arg is fine).
      Do not change endpoint path or response shape.
      **Verify:** route still imports and backend compiles: `cd backend && uv run python -m compileall src`.

- [x] **Step 7: Protect `POST /repos/{owner}/{name}/ingest`**
      File: `backend/src/talkingcode/routes/repo_routes.py`.
      Add auth dependency to `start_ingestion(...)` route.
      Keep existing body behavior (`StartIngestionRequest | None`) unchanged.
      **Verify:** same compile check as Step 6.

- [x] **Step 8: Protect `POST /repos/ingest-owned`**
      File: `backend/src/talkingcode/routes/repo_routes.py`.
      Add auth dependency to `start_owned_repo_ingestion(...)` route.
      **Verify:** same compile check as Step 6.

- [x] **Step 9: Confirm read routes remain public**
      File: `backend/src/talkingcode/routes/repo_routes.py`.
      Ensure no auth dependency is attached to:
      - `GET /repos`
      - `GET /repos/{owner}/{name}`
      - `GET /repos/{owner}/{name}/runs`
      **Verify:** inspect file manually and ensure these signatures do not include auth dep.

- [x] **Step 10: Confirm chat routes remain unchanged/public**
      File: `backend/src/talkingcode/routes/chat_routes.py`.
      Do not add any ingestion-key dependency here.
      **Verify:** `git diff -- backend/src/talkingcode/routes/chat_routes.py` shows no changes.

- [x] **Step 11: Remove public ingest action wiring from repos page**
      File: `talkingcode-frontend/src/routes/repos/+page.svelte`.
      Remove `onIngest` handler and any calls to `repoService.startIngestion(...)`.
      Keep list loading and run-history refresh behavior intact.
      **Verify:** no `startIngestion` symbol used in this file.

- [x] **Step 12: Remove ingest button from repo card UI**
      File: `talkingcode-frontend/src/lib/components/domain/RepoCard.svelte`.
      Remove the public "Ingest now" trigger/button and related callback prop.
      Keep "Show history" / "Hide history" behavior unchanged.
      Keep existing Tailwind/shadcn style patterns.
      **Verify:** no visible control in this component that triggers ingestion POST.

- [x] **Step 13: Add backend tests for protected POST routes**
      File: create/update test module under `backend/tests/` following existing test style.
      Add tests for each protected POST endpoint verifying:
      - no key => `401`
      - wrong key => `401`
      - correct `X-API-Key` passes auth layer
      - correct `api_key` query passes auth layer
      Mock downstream services if needed; this is auth-gate testing, not ingestion internals.
      **Verify:** `cd backend && uv run pytest -q` passes.

- [ ] **Step 14: Add backend tests for public routes**
      File: same/new backend test module.
      Verify `GET /repos` is accessible without key and chat route remains accessible without ingestion key.
      Keep tests focused on route access policy.
      **Verify:** `cd backend && uv run pytest -q` passes.

- [ ] **Step 15: Document cron usage for protected ingestion**
      File: update an existing docs file (`README.md` or backend README).
      Add a short section with:
      - env var name `INGESTION_API_KEY`
      - curl with header auth
      - curl with query auth
      - note that repo list endpoints remain public/read-only
      **Verify:** commands are copy-pastable and use real route paths.

- [ ] **Step 16: End-to-end manual verification**
      Start backend + frontend with `INGESTION_API_KEY` set.
      Check:
      - protected POST routes return `401` without key
      - protected POST routes accept valid key
      - `/repos` UI still shows repositories and ingestion history
      - no UI button allows anonymous ingestion trigger
      **Verify:** capture exact commands used and results in a short note under this step before checking it off.

## Tests

- Run backend checks after Steps 10, 14, and 16:
  - `cd backend && uv run python -m compileall src`
  - `cd backend && uv run pytest -q`
- Run frontend checks after Step 12:
  - `cd talkingcode-frontend && pnpm check` (or project standard validation command)
- Minimum behavior assertions:
  - protected POST repo routes require valid ingestion key
  - GET repo visibility routes stay public
  - chat routes stay public
  - repos UI is read-only for ingestion actions

## Verification

- Add to `.env`:
  - `INGESTION_API_KEY=your-secret`
- Without key, verify `401`:
  - `curl -i -X POST "http://localhost:8000/repos/ingest-owned"`
  - `curl -i -X POST "http://localhost:8000/repos/chidi/chatGITpt/ingest"`
- With valid header key, verify authorized:
  - `curl -i -X POST "http://localhost:8000/repos/ingest-owned" -H "X-API-Key: your-secret"`
- With valid query key, verify authorized:
  - `curl -i -X POST "http://localhost:8000/repos/ingest-owned?api_key=your-secret"`
- Public reads/chat without key:
  - `curl -i "http://localhost:8000/repos"`
  - `curl -i "http://localhost:8000/health"`
- Frontend check:
  - open `/repos`
  - confirm tracked repos and ingestion timestamps are visible
  - confirm no button/action exists for anonymous ingestion trigger
