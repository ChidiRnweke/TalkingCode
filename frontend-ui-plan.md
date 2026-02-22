# Blueprint: TalkingCode UI (Agentic RAG, svelte-ui)

## Executor Instructions

1. Read this file every loop.
2. Execute only the next unchecked step.
3. Follow `DESIGN_SYSTEM.md` and locked UI contracts.
4. Verify each step before checking off.
5. Commit each completed step.

## Context

This UI blueprint is for whitebox agentic chat. Users should clearly see planner/tool activity and
active filters, but never see raw tool payload results. Visual direction remains Editorial Light.

## Scope

**In scope:**

- Design-token-consistent agentic chat layout.
- Locked `svelte-ai-elements` inventory for chat and controls.
- Tool timeline, planner banner, filter visibility, and assistant actions.
- Responsive behavior and focused component tests.

**Out of scope:**

- Payload rendering from tool outputs.

## Architecture Decisions

- Use `svelte-ai-elements` primitives for chat-first surfaces.
- Mandatory action row uses `Actions` + `Action` with: Retry / Copy / Show Filters.
- Tool names and visible args/filters are shown; payload bodies are hidden.
- All colors/spacing/typography derive from `DESIGN_SYSTEM.md` tokens.

## Interfaces and Models

UI components consume contracts from `frontend-svelte-plan.md`:

- `AgentPlanView`
- `ToolCallTimelineItem`
- `RetrievalFilterView`
- `AgentStreamEvent`

## Locked UI Inventory

Required `svelte-ai-elements` components:

- `new-message` suite (`Message`, `MessageContent`, `MessageResponse`)
- `prompt-input`
- `model-selector`
- `sources`
- `loader`, `shimmer`
- `actions` (`Actions`, `Action`)

Required installs include:

- `pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/new-message.json`
- `pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/action.json`

## Layout Blueprint (Locked)

- Desktop: nav `240px`, conversation rail `320px`, main chat canvas flexible.
- Tablet: collapsible nav + single chat column.
- Mobile: single-column chat, rail in drawer/sheet.
- Sticky composer at bottom of chat canvas.
- Message widths: assistant `72ch`, user `60ch`.

## Component Contract Table

| Component | Required Props | Must Render Using | Notes |
| --- | --- | --- | --- |
| `AgentPlanBanner.svelte` | `plan: AgentPlanView | null`, `isPlanning: boolean` | tokenized `Card` | Shows intent + filters summary. |
| `ToolTimeline.svelte` | `items: ToolCallTimelineItem[]`, `isRunning: boolean` | tokenized container + `Loader` | Newest item first. |
| `ToolTimelineItem.svelte` | `item: ToolCallTimelineItem` | tokenized row + `Badge` | Show tool name, repo/path args, status, duration. |
| `FilterChips.svelte` | `filters: RetrievalFilterView` | tokenized `Badge` chips | Show areas/languages/file types/path hints. |
| `ChatMessage.svelte` | `message`, `isStreaming?` | `Message`, `MessageContent`, `MessageResponse` | Role maps to user/assistant visuals. |
| `ChatMessageActions.svelte` | `onRetry`, `onCopy`, `onToggleFilters`, `filtersOpen` | `Actions`, `Action` | Exactly 3 actions required. |

Hard rules:

- Never render tool payload `content`.
- `Show Filters` toggles planner + visible args only.
- Long paths truncate in row, full value in tooltip/title.

## Plan

- [ ] **Step 1: Ensure token/theming baseline is applied**
      Confirm token usage from `DESIGN_SYSTEM.md` in app styles and component theming.
      Verify: no default Tailwind palette leakage.

- [ ] **Step 2: Install and theme required `svelte-ai-elements` components**
      Install required registry components and apply tokenized theme overrides.
      Verify: showcase page demonstrates themed primitives.

- [ ] **Step 3: Build planner/timeline/filter domain UI components**
      Implement plan banner, tool timeline, timeline item, and filter chips.
      Verify: all status states render correctly.

- [ ] **Step 4: Integrate assistant action row**
      Add Retry/Copy/Show Filters actions under assistant responses using `Actions`/`Action`.
      Verify: handlers fire and accessibility labels/tooltips exist.

- [ ] **Step 5: Integrate responsive layout behavior**
      Apply locked desktop/tablet/mobile layout and sticky composer behavior.
      Verify: layout works at common breakpoints.

- [ ] **Step 6: Add focused component tests**
      Cover action row constraints, timeline rendering, filter toggle, and payload privacy.
      Verify: frontend test suite passes.

- [ ] **Step 7: Run UI audit and finalize**
      Run audit checklist and align any drift back to `DESIGN_SYSTEM.md`.
      Verify: no major anti-patterns remain.

## Tests

- `pnpm --dir frontend check`
- `pnpm --dir frontend test`

## Verification

1. `pnpm --dir frontend check`
2. `pnpm --dir frontend test`
3. Ask a tool-calling question and confirm:
   - planner banner appears,
   - timeline updates in real time,
   - Retry/Copy/Show Filters actions work,
   - payload data is hidden.
