# Blueprint: TalkingCode Frontend UI (svelte-ui)

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. Read this file at the start of every loop.
2. Execute only the next unchecked step.
3. Do not build page components before design tokens are established.
4. Follow `svelte-ui` conventions and anti-pattern checks.
5. Verify each step before checking it off.
6. Commit each completed step with `blueprint: [step title]`.

## Context

This subplan defines the visual system and UI composition for TalkingCode V1. It is separate from
frontend architecture (`frontend-svelte-plan.md`) so visual decisions remain coherent and reusable
across pages.

User-selected direction is **Editorial Light**: light, warm, readable, with expressive serif
headings and restrained, intentional accents. The result should feel crafted rather than default
Tailwind/shadcn output.

This plan must keep complexity controlled: introduce a strong design system and include only
targeted component tests for critical UI behavior.

## Scope

**In scope:**

- Design tokens (color, typography, spacing, radii, shadows) in `frontend/src/app.css`.
- Tailwind + shadcn variable remap to design tokens.
- Primitive components and layout shell components.
- Domain components for chat/repos/pipeline/settings pages.
- Empty states, skeleton states, responsive checks, and limited component tests.

**Out of scope:**

- Pixel-perfect marketing site polish beyond core app surfaces.
- Large visual animation system or bespoke motion library.

## Architecture Decisions

- UI tokens are single source of truth in CSS custom properties.
- Typography pairing avoids Inter/Roboto/Arial as primary fonts.
- Neutrals are warm-tinted, not pure white/gray defaults.
- shadcn components are themed immediately; default style is not accepted.
- Use primitives (`Button`, `Input`, `Card`, `Badge`) instead of raw tags in page code.
- Keep tests focused on high-value behavior (render states, variants, interaction hooks).

## Interfaces and Models

UI contract expectations:

- Token variables in `frontend/src/app.css` and mapped usage in Tailwind/shadcn semantics.
- Primitive props for consistent sizing/variants.
- Domain components accept frontend domain models from architecture layer, not API schemas.

## Plan

- [ ] **Step 1: Establish Editorial Light design tokens**
      Define token blocks in `frontend/src/app.css`: warm surfaces, editorial text palette,
      accent color, semantic colors, type scale, spacing scale, radius, and shadow tokens.
      Set fonts in `frontend/src/app.html` (display + body + mono).
      Verify: app loads with fonts and token references; no default Tailwind blue reliance.

- [ ] **Step 2: Map Tailwind and shadcn semantics to tokens**
      Configure Tailwind extensions and remap shadcn variables (`--background`, `--foreground`,
      `--primary`, `--muted`, `--border`, etc.) to token set.
      Verify: generated components inherit project look without manual per-component overrides.

- [ ] **Step 3: Implement primitive wrappers and enforce usage**
      Build `frontend/src/lib/components/primitives/` wrappers for `Button`, `Input`, `Card`,
      and `Badge` with project defaults. Replace raw usage in route components where applicable.
      Verify: component examples render and style variants are consistent.

- [ ] **Step 4: Build layout system components**
      Implement `AppShell`, `Sidebar`, `Header`, and `MainContent` components under
      `frontend/src/lib/components/layout/` with responsive behavior for desktop/mobile.
      Verify: all app routes render inside consistent shell on common viewport sizes.

- [ ] **Step 5: Build domain components for key product surfaces**
      Implement/finish components for chat messages/input, conversation list, repo cards,
      pipeline status, model selector, empty states, and skeleton states.
      Verify: each route displays correct empty/loading/content states.

- [ ] **Step 6: Add lightweight component tests for critical UI behavior**
      Add a limited test set (no explosion):
      - primitive variant rendering (`Button`, `Card`),
      - chat message role styling and source visibility,
      - empty vs loaded state switch for one page-level domain component.
      Verify: `pnpm --dir frontend test` passes.

- [ ] **Step 7: Run blandness audit and accessibility sanity checks**
      Audit for anti-patterns: default colors, raw controls, inconsistent spacing, weak hierarchy.
      Ensure keyboard focus visibility and adequate contrast on primary interactions.
      Verify: manual audit checklist completed; no obvious contrast/focus regressions.

## Tests

- `pnpm --dir frontend check`
- `pnpm --dir frontend test`

Recommended component test scope (balanced):

- 2-4 primitive/component rendering and variant tests.
- 1-2 domain component state-switch tests.
- Avoid broad snapshot-only coverage.

## Verification

1. `pnpm --dir frontend dev`
2. Validate routes `/`, `/repos`, `/pipeline`, `/settings` on desktop + mobile widths.
3. Confirm all colors/typography derive from CSS vars, not Tailwind defaults.
4. Confirm empty and skeleton states exist where lists/streams can be pending/empty.
5. `pnpm --dir frontend check`
6. `pnpm --dir frontend test`
