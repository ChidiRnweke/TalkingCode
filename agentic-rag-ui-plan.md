# Blueprint: Agentic RAG UI (svelte-ui)

## Executor Instructions

1. Read this file every loop.
2. Execute only the next unchecked step.
3. Follow `DESIGN_SYSTEM.md` and `frontend-ui-plan.md` locked contracts.
4. Verify each step before checking off.
5. Commit each completed step.

## Context

This blueprint defines UI behavior for whitebox agentic chat. The interface must expose planning
and tool-call process clearly while preserving payload privacy. The user should see which tools were
called and which filters were used, with a polished Editorial Light layout.

This is not a generic chat polish pass; it is a constrained instrumentation UI.

## Scope

**In scope:**

- Tool timeline rendering and filter visibility in chat.
- `svelte-ai-elements/actions` integration for assistant message controls.
- Layout and interaction rules for planner/tool states.
- Component tests for whitebox states and action affordances.

**Out of scope:**

- Displaying tool payload result bodies.

## Architecture Decisions

- Use `svelte-ai-elements` `Actions` + `Action` on assistant messages.
- Mandatory action buttons: Retry, Copy, Show Filters.
- Tool timeline remains visible and compact in chat flow.
- Tool names and repo/path filters are visible; raw tool outputs are never rendered.

## Interfaces and Models

UI components consume models from `agentic-rag-frontend-plan.md`:

- `AgentPlanView`
- `ToolCallTimelineItem`
- `AgentStreamEvent`
- `RetrievalFilterView`

## Locked UI Inventory (Agentic Additions)

- Install `actions` component:
  - `pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/action.json`
- Required usage:
  - `Actions` container under assistant responses
  - `Action` buttons for Retry / Copy / Show Filters

New domain components:

- `AgentPlanBanner.svelte`
- `ToolTimeline.svelte`
- `ToolTimelineItem.svelte`
- `FilterChips.svelte`

## Component Contract Table (Agentic Additions)

| Component | Required Props | Must Render Using | Notes |
| --- | --- | --- | --- |
| `AgentPlanBanner.svelte` | `plan: AgentPlanView | null`, `isPlanning: boolean` | tokenized `Card` + text primitives | Shows current intent + filters summary. |
| `ToolTimeline.svelte` | `items: ToolCallTimelineItem[]`, `isRunning: boolean` | tokenized container + `Loader` | Collapsible section; newest item top. |
| `ToolTimelineItem.svelte` | `item: ToolCallTimelineItem` | tokenized row + status `Badge` | Show `toolName`, repo/path args, duration, status icon. |
| `FilterChips.svelte` | `filters: RetrievalFilterView` | tokenized `Badge` chips | Show areas/languages/file_types/path hints. |
| `ChatMessageActions.svelte` | `onRetry`, `onCopy`, `onToggleFilters`, `filtersOpen` | `Actions`, `Action` | Exactly three actions required. |

Hard rules:

- Never render tool payload `content` in any UI component.
- `Show Filters` toggles only planner and visible tool args, not payload.
- Timeline rows truncate long paths but keep full path in tooltip/title attribute.

## Plan

- [ ] **Step 1: Install and theme `actions` component**
      Add `svelte-ai-elements/actions` and map it to Editorial Light tokens/spacing.
      Verify: demo row renders with three required actions styled correctly.

- [ ] **Step 2: Build planner + tool timeline components**
      Implement `AgentPlanBanner`, `ToolTimeline`, `ToolTimelineItem`, and `FilterChips`.
      Verify: components render all required states (planning/running/finished/error).

- [ ] **Step 3: Integrate action row into assistant message surfaces**
      Update chat domain components to use `Actions`/`Action` with Retry/Copy/Show Filters.
      Verify: action handlers trigger expected store/controller events.

- [ ] **Step 4: Integrate timeline and plan banner into chat layout**
      Place plan banner near top of active chat pane and timeline beneath recent assistant turn.
      Verify: layout works on desktop/tablet/mobile and remains readable.

- [ ] **Step 5: Add component tests for whitebox interaction contract**
      Test action visibility, filter toggle behavior, timeline status rendering, and no payload leak.
      Verify: frontend test suite passes.

- [ ] **Step 6: Run UI audit with agentic checklist**
      Apply audit flow and verify no anti-pattern regressions in tokens, spacing, and controls.
      Verify: audit notes complete and `DESIGN_SYSTEM.md` updated if needed.

## Tests

- `pnpm --dir frontend check`
- `pnpm --dir frontend test`

Must-have cases:

- `ChatMessageActions` renders exactly three required actions.
- `ToolTimelineItem` shows tool name + visible args + status without payload body.
- `Show Filters` toggles planner/filter panel deterministically.

## Verification

1. `pnpm --dir frontend check`
2. `pnpm --dir frontend test`
3. Ask a question that triggers tool calls and confirm:
   - planner banner visible,
   - timeline updates in real-time,
   - Retry/Copy/Show Filters actions work,
   - tool payloads remain hidden.
