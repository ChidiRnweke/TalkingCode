# Blueprint: TalkingCode V1 Master Plan

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. **Read this file first.** Every loop, re-read this file before doing anything.
2. **Do the next unchecked step.** Find the first `- [ ]` item. Do that. Only that.
3. **Delegate to subplans when referenced.** When a step points to a subplan file, execute that
   subplan in order until its verification passes.
4. **Verify before checking off.** Run the verification in this step (and referenced subplan).
5. **Commit after each completed step.** `git add -A && git commit -m "blueprint: [step title]"`
6. **Do not skip dependencies.** Steps are ordered intentionally.
7. **If blocked, annotate.** Add a short blocker note under the step and continue if possible.
8. **Keep blueprint files updated.** Mark completed items and add discovery notes for later steps.

## Context

TalkingCode V1 is a full-stack BFF monorepo: SvelteKit frontend + FastAPI backend + Postgres with
pgVector. The product ingests public GitHub code, embeds it with OpenAI embeddings, and serves a
chat experience that answers questions with retrieved code context.

This master plan orchestrates execution through three implementation blueprints: backend
architecture (`python-swe`), frontend architecture (`svelte-swe`), and frontend design system/UI
(`svelte-ui`). This keeps each plan granular and pattern-constrained while preserving one top-level
dependency graph.

User decisions captured in this planning round: full V1 scope, balanced testing strategy,
strict frontend layering from day one, OpenAI embeddings required, and UI direction set to
**Editorial Light**.

## Scope

**In scope:**

- Full V1 backend + frontend + UI implementation planning.
- Local development runtime via Docker Compose.
- End-to-end integration and script-based verification.
- Test-first mindset for critical behavior with balanced coverage depth.

**Out of scope:**

- Auth/authorization system beyond static environment configuration.
- Private repository ingestion.
- Multi-user tenancy and roles.
- Production hardening (autoscaling, full observability stack, secrets manager).
- Advanced retrieval upgrades (hybrid search/rerankers) beyond baseline vector retrieval.

## Architecture Decisions

- Plan-of-plans approach: this file controls sequencing; subplans own implementation detail.
- Backend follows `python-swe` layering rules strictly.
- Frontend follows `svelte-swe` layering rules strictly.
- UI implementation follows `svelte-ui` with Editorial Light design system before components.
- Embedding provider is OpenAI (model configurable; default expected as `text-embedding-3-small`).
- Verification emphasizes passing tests plus scriptable e2e checks across backend/frontend.

## Interfaces and Models

Interface and model definitions are delegated to subplans:

- `backend-python-plan.md` owns backend Protocols, dataclasses, ORM boundaries.
- `frontend-svelte-plan.md` owns frontend service interfaces, controller contracts, stores.
- `frontend-ui-plan.md` owns design tokens, primitive contracts, and visual conventions.

## Plan

- [ ] **Step 1: Scaffold monorepo runtime and baseline structure**
      Create runtime foundations (`docker-compose.yml`, backend/frontend skeletons, env examples,
      package manifests, source roots). Keep structure compatible with all three subplans.
      Verify: `docker compose config` succeeds.

- [ ] **Step 2: Execute backend blueprint to API-ready state**
      Follow `backend-python-plan.md` from top to bottom. Complete all unchecked steps there,
      including tests and verification, before checking this master step.
      Verify: backend subplan verification commands pass.

- [ ] **Step 3: Execute frontend architecture blueprint**
      Follow `frontend-svelte-plan.md` from top to bottom. Complete all unchecked steps there,
      including typed API generation and architecture checks.
      Verify: frontend architecture subplan verification commands pass.

- [ ] **Step 4: Execute frontend UI blueprint (Editorial Light)**
      Follow `frontend-ui-plan.md` from top to bottom. Implement tokens, theming, primitives, page
      composition rules, and limited component tests.
      Verify: UI subplan verification commands pass.

- [ ] **Step 5: Integrate and run end-to-end verification scripts**
      Add or finalize scripts that boot backend and validate API from frontend-side script calls,
      then run full integration flow (sync repos -> run pipeline -> chat stream).
      Verify: all commands in `## Verification` pass.

## Tests

Required aggregate quality bar for V1:

- Balanced backend unit + integration coverage of critical flows.
- Frontend type checks and architecture-safe tests.
- Lightweight component tests for core UI components only (avoid explosion).
- End-to-end script checks proving cross-service integration.

## Verification

Run after all steps are checked off:

1. `docker compose up --build -d`
2. `pytest backend/tests/unit -q`
3. `pytest backend/tests/integration -q`
4. `pnpm --dir frontend check`
5. `pnpm --dir frontend test` (if configured)
6. `pnpm --dir frontend run verify:e2e` (script that calls backend APIs from frontend context)
7. `curl http://localhost:8000/api/health`
8. Validate flow: repos sync, pipeline run, chat response stream with sources.
