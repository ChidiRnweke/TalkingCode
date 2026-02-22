# Blueprint: TalkingCode Frontend Architecture (svelte-swe)

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. Read this file at the start of every loop.
2. Execute only the next unchecked step.
3. Follow `svelte-swe` layering rules strictly.
4. Verify each step before checking it off.
5. Commit each completed step with `blueprint: [step title]`.
6. If blocked, leave a note under the step and continue where possible.

## Context

This subplan defines frontend engineering architecture for TalkingCode V1 in SvelteKit. It focuses
on layer boundaries and integration contracts, not visual design (handled separately in
`frontend-ui-plan.md`).

The frontend must consume backend APIs through generated OpenAPI types and openapi-fetch, keep
business logic out of route files, and maintain strict separation across services, controllers,
factory assembly, stores, and Svelte route components.

This plan depends on backend API availability from `backend-python-plan.md` and feeds into UI work
that applies design tokens and component conventions.

## Scope

**In scope:**

- Frontend scaffold, typed API client generation, and environment wiring.
- Service interfaces + implementations mapped from OpenAPI schemas.
- Controller orchestration layer and factory assembly.
- Route loaders/actions with strict boundary discipline.
- Client stores populated from loader data.
- Script-based frontend verification that calls backend endpoints.

**Out of scope:**

- Visual theming and design system decisions (UI subplan handles this).
- New backend feature work beyond client contract alignment.

## Architecture Decisions

- Enforce strict layering from day one (`+page.svelte` UI only; no direct service calls).
- Route files coordinate loading/actions only; business logic sits in controllers/services.
- Services wrap API client and map OpenAPI schemas to domain models.
- Controllers orchestrate multi-service operations.
- `AppFactory` constructs concrete dependencies; no logic in factory.
- Use Svelte runes stores as client state singletons hydrated from loader data.

## Interfaces and Models

Expected frontend contracts:

- `src/lib/models/*` domain interfaces for chat/repos/pipeline/settings.
- `src/lib/services/I*Service.ts` interfaces + concrete implementations.
- `src/lib/controllers/*Controller.ts` orchestration classes.
- `src/lib/factories/AppFactory.ts` assembly methods.
- `src/lib/stores/*.svelte.ts` state containers.
- `src/lib/api/client.ts` + generated `schema.d.ts`.

## Plan

- [ ] **Step 1: Scaffold frontend project and baseline scripts**
      Initialize SvelteKit TypeScript project under `frontend/`, configure package scripts for
      `dev`, `check`, `test`, and API generation.
      Verify: `pnpm --dir frontend install` and `pnpm --dir frontend check` run.

- [ ] **Step 2: Configure typed API client and schema generation**
      Implement `src/lib/api/client.ts` using `openapi-fetch` and env-driven `PUBLIC_API_URL`.
      Add generation script to produce `src/lib/api/schema.d.ts` from backend OpenAPI.
      Verify: `pnpm --dir frontend run generate:api` and `pnpm --dir frontend check` pass.

- [ ] **Step 3: Define domain models and service interfaces**
      Add `src/lib/models/*` and `src/lib/services/I*Service.ts` interfaces for chat/repos/
      pipeline/settings contracts.
      Verify: TypeScript check passes with model/interface imports.

- [ ] **Step 4: Implement concrete services with schema-to-domain mapping**
      Add service implementations in `src/lib/services/*Service.ts` that call typed API client,
      map response payloads to domain models, and normalize service-level errors.
      Verify: service unit tests (or focused integration mocks) pass.

- [ ] **Step 5: Implement controllers and factory assembly**
      Add controller classes in `src/lib/controllers/` and concrete assembly in
      `src/lib/factories/AppFactory.ts`. Ensure controllers take interfaces, not concrete types.
      Verify: route-level imports compile and pass type checks.

- [ ] **Step 6: Implement route loaders/actions with strict boundaries**
      Create `+layout.server.ts` and route `+page.server.ts` files for `/`, `/repos`, `/pipeline`,
      `/settings`. Keep route files thin: validation + delegation + response mapping only.
      Verify: route loader/action tests or smoke checks pass.

- [ ] **Step 7: Implement stores and hydrate from loader data**
      Add runes stores under `src/lib/stores/*.svelte.ts` and populate via `$effect` in route
      components. No network calls in stores.
      Verify: frontend check passes and pages render with loader-provided state.

- [ ] **Step 8: Add frontend-side integration scripts calling backend APIs**
      Add scripts under `frontend/scripts/` that call backend endpoints from frontend context
      (health, repos, pipeline status, chat request shape) for CI-friendly integration checks.
      Verify: `pnpm --dir frontend run verify:e2e` passes against running backend.

- [ ] **Step 9: Final architecture audit against svelte-swe rules**
      Audit route/components for layer violations (service calls in components, business rules in
      routes, leaked OpenAPI schema types outside services) and fix.
      Verify: lint/type/tests pass and audit notes are clean.

## Tests

- `pnpm --dir frontend check`
- `pnpm --dir frontend test` (if configured)
- `pnpm --dir frontend run verify:e2e`

Minimum coverage focus:

- Service response mapping and error handling.
- Controller orchestration behavior for chat/repos/pipeline flows.
- Loader/action happy-path and auth/validation edge handling where applicable.

## Verification

1. Start backend and frontend (`docker compose up -d` or local dev servers).
2. `pnpm --dir frontend run generate:api`
3. `pnpm --dir frontend check`
4. `pnpm --dir frontend test` (if available)
5. `pnpm --dir frontend run verify:e2e`
6. Manual sanity:
   - `/repos` loads and sync action wired.
   - `/pipeline` loads status/history.
   - `/` sends chat request and handles streaming state.
