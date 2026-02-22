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
- Root `DESIGN_SYSTEM.md` is the canonical UI spec and must be referenced from `AGENTS.md`.
- Use `svelte-ai-elements` as the default chat UI vocabulary to reduce UI implementation drift.
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

## Locked UI Inventory (Low Degrees of Freedom)

Install and use these `svelte-ai-elements` components as the primary chat surface primitives:

- `new-message` (Message suite):
  - `Message`
  - `MessageContent`
  - `MessageResponse`
  - `MessageActions`
  - `MessageAction`
  - `MessageBranch` (optional for retry variants)
- `prompt-input` for multiline chat input + submit affordance.
- `conversation` for conversation timeline shell when applicable.
- `model-selector` for explicit model picking in settings/chat composer.
- `sources` for retrieved-context citation rendering under assistant output.
- `loader` + `shimmer` for loading states (avoid spinner-only states).

Install command references:

- `pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/new-message.json`
- Repeat for each required registry component used in this blueprint.

Component mapping by route:

- `/` (chat page)
  - Chat transcript rows: `Message` + `MessageContent` + `MessageResponse`
  - Assistant actions row: `MessageActions` + `MessageAction` (copy, retry)
  - Input area: `PromptInput`
  - Model picker: `ModelSelector`
  - Citations: `Sources`
  - Pending state: `Loader`/`Shimmer` skeleton blocks
- `/repos`
  - Keep custom `RepoCard`, but loading placeholders must use `Shimmer`
- `/pipeline`
  - Keep custom `PipelineStatus`, but running states must use `Loader`
- `/settings`
  - Use `ModelSelector` as the primary interactive element

Layout blueprint (locked):

- Desktop (`>= 1024px`):
  - 3-column shell: left nav `240px`, conversation list `320px`, chat canvas `minmax(0, 1fr)`
  - Sticky composer at bottom of chat canvas with tokenized surface and border
- Tablet (`768px - 1023px`):
  - 2-column shell: collapsible nav + full-width chat canvas
- Mobile (`< 768px`):
  - Single-column stacked flow; conversation list behind a sheet/drawer toggle

Spacing and hierarchy lock:

- Message row vertical gap: `--space-4`
- Section-to-section gap: `--space-8`
- Page header bottom margin: `--space-6`
- Composer padding: `--space-4`
- Assistant message max width: `72ch`
- User message max width: `60ch`

## Component Contract Table (Execution Locked)

Use these exact contracts to avoid ad-hoc UI composition.

| Domain Component | Required Props | Must Render Using | Notes |
| --- | --- | --- | --- |
| `ChatMessage.svelte` | `message: ChatMessageView`, `isStreaming?: boolean` | `Message`, `MessageContent`, `MessageResponse` | `message.role` maps to `from="user" | "assistant"`; stream state shows shimmer tail. |
| `ChatMessageActions.svelte` | `messageId: string`, `canRetry: boolean`, `onCopy: () => void`, `onRetry: () => void` | `MessageActions`, `MessageAction` | Only allow retry on assistant messages. |
| `ChatSources.svelte` | `sources: SourceItem[]` | `Sources` | Hidden when `sources.length === 0`; visible under assistant response only. |
| `ChatComposer.svelte` | `value: string`, `isSubmitting: boolean`, `selectedModel: string`, `models: ModelOption[]`, `onSubmit: (value: string) => void`, `onModelChange: (id: string) => void` | `PromptInput`, `ModelSelector` | Composer stays sticky; submit disabled while streaming/submitting. |
| `ConversationRail.svelte` | `items: ConversationSummary[]`, `activeId: string | null`, `onSelect: (id: string) => void`, `onCreate: () => void` | `Conversation` (or tokenized list wrapper) | On mobile render in drawer/sheet; desktop fixed width `320px`. |
| `RepoCard.svelte` | `repo: RepositorySummary` | tokenized `Card` primitive + `Badge` | No raw borders/colors outside tokens. |
| `PipelineStatus.svelte` | `run: PipelineRunView | null`, `isRunning: boolean` | tokenized `Card`, `Loader`, status `Badge` | Running state must use `Loader`, not spinner-only glyph. |
| `SettingsModelSelector.svelte` | `models: ModelOption[]`, `value: string`, `onChange: (id: string) => void` | `ModelSelector` | This is the primary control on `/settings`. |
| `EmptyState.svelte` | `title: string`, `description: string`, `ctaLabel?: string`, `onCta?: () => void` | tokenized `Card` + icon slot | Must be used for empty chat/repos/pipeline surfaces. |
| `SkeletonChat.svelte` | `rows?: number` | `Shimmer` | Row structure should mirror final message layout. |

Data shape contracts used by UI components:

- `ChatMessageView`: `{ id: string; role: 'user' | 'assistant'; content: string; sources: SourceItem[]; createdAt: string; modelUsed?: string }`
- `SourceItem`: `{ id: string; filePath: string; repoName: string; startLine?: number; endLine?: number; url?: string }`
- `ModelOption`: `{ id: string; label: string; provider?: string }`
- `ConversationSummary`: `{ id: string; title: string; createdAt: string }`
- `RepositorySummary`: `{ id: string; name: string; owner: string; language?: string; description?: string; url: string }`
- `PipelineRunView`: `{ id: string; status: 'running' | 'completed' | 'failed'; startedAt: string; finishedAt?: string; reposProcessed: number; chunksCreated: number; error?: string }`

Hard rules for executor:

- Do not pass generated OpenAPI schema types directly into UI components.
- Map transport payloads to these domain contracts in frontend services/controllers first.
- Do not replace required `svelte-ai-elements` components with bespoke alternatives unless blocked; if blocked, add a blocker note and the fallback used.

## Plan

- [ ] **Step 1: Establish Editorial Light design tokens**
      Create/update root `DESIGN_SYSTEM.md` first with visual direction, palette, typography,
      spacing, radius, conventions, and anti-patterns. Ensure `AGENTS.md` references this file.
      Define token blocks in `frontend/src/app.css`: warm surfaces, editorial text palette,
      accent color, semantic colors, type scale, spacing scale, radius, and shadow tokens.
      Set fonts in `frontend/src/app.html` (display + body + mono).
      Verify: `DESIGN_SYSTEM.md` exists in root, `AGENTS.md` references it, app loads with fonts
      and token references, and no default Tailwind blue reliance.

- [ ] **Step 2: Map Tailwind and shadcn semantics to tokens**
      Configure Tailwind extensions and remap shadcn variables (`--background`, `--foreground`,
      `--primary`, `--muted`, `--border`, etc.) to token set.
      Verify: generated components inherit project look without manual per-component overrides.

- [ ] **Step 2.5: Install and theme svelte-ai-elements set**
      Install `new-message`, `prompt-input`, `conversation`, `model-selector`, `sources`,
      `loader`, and `shimmer` from the registry. Apply design token classes/variables so imported
      components match Editorial Light appearance and spacing rules.
      Verify: component showcase route or story page renders all imported components themed.

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
      For chat surfaces, prefer composition around `svelte-ai-elements` message/prompt primitives
      instead of bespoke chat bubble components.
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
      Also run the audit flow from `.claude/skills/svelte-ui/references/audit.md` and update
      `DESIGN_SYSTEM.md` if conventions changed during implementation.
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
