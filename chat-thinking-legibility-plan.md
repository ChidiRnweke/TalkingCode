# Blueprint: GPT-Inspired Chat Legibility and Thinking Panel

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. **Read this file first.** Every loop, re-read this file before doing anything.
2. **Do the next unchecked step.** Find the first `- [ ]` item. Do that. Only that.
3. **Verify before checking off.** Run the verification described in the step.
4. **Commit after each step.** `git add -A && git commit -m "blueprint: [step title]"`
5. **Don't skip ahead.** Steps are dependency ordered.
6. **Follow existing patterns.** Reuse current chat store, stream contract, and UI primitives.
7. **If blocked, document and continue.** Add notes under the step and move forward.
8. **Update this file.** Keep this blueprint as the source of truth.

---

## Context

TalkingCode already has most of the pieces required for GPT-style thought inspection: a reasoning
trigger row in each assistant message, a right-side detail panel, and streaming events for
iteration/plan/tool lifecycle. However, the current wiring does not match the intended UX.

The current right panel opens from an action icon, not from clicking the thinking row. In addition,
chat body typography is less legible than desired because assistant content is rendered with compact
text styles in the inner message content container. The stream parser is strict and can drop backend
events due to field mismatch (`message`/`visible_args` differences), making thought/tool state feel
incomplete during live runs.

This feature should produce a chat experience inspired by GPT and Claude: higher legibility in the
answer body, and click-to-open thinking details on the right side, while preserving TalkingCode's
own visual identity.

## Scope

**In scope:**

- Chat-page-only readability improvements (assistant content + thinking row)
- Thinking row click opens right-side detail panel
- Right panel UX refinement for desktop and mobile behavior
- Stream parser/contract alignment so reasoning/tool events are reliably consumed
- Removal of irrelevant chat-only controls if they duplicate the new interaction

**Out of scope:**

- Non-chat page redesign
- Pixel-perfect imitation of GPT/Claude
- Full conversation history architecture beyond current stream behavior

## Architecture Decisions

1. Use existing `TurnDetailPanel` as the right-side activity panel rather than introducing new panel infrastructure.
2. Use the existing reasoning row (`ReasoningTrigger`) as the primary open action for details.
3. Keep state in `chatStore` and route-level `detailPanelMessageId` as source of truth for panel visibility.
4. Preserve strict frontend parsing but update schemas to reflect actual backend event payload fields.
5. Improve legibility at component level (chat message components), not global typography tokens.

## Interfaces and Models

- Frontend stream event union remains `AgentStreamEvent`.
- `ChatMessage.planText` and `ChatMessage.toolCalls` remain the data source for panel rendering.
- `ReasoningTrigger` interface must accept click handlers so parent messages can open panel.
- SSE parser must accept backend-emitted `message` fields and optional `visible_args` where applicable.

## Plan

- [ ] **Step 1: Wire thinking row click to open right panel**
      Update reasoning trigger/component props so assistant message can pass click behavior, and wire
      the click to `onOpenDetail(message.id)`.
      Files: `talkingcode-frontend/src/lib/components/ai-elements/reasoning/ReasoningTrigger.svelte`,
      `talkingcode-frontend/src/lib/components/domain/AssistantMessage.svelte`.
      Verify: clicking "Thinking/Thought for X seconds" opens `TurnDetailPanel` for that turn.

- [ ] **Step 2: Improve assistant text legibility**
      Increase readability of assistant response text (size/weight/leading/measure) while keeping
      user bubbles compact and preserving design-system tone.
      Files: `talkingcode-frontend/src/lib/components/ai-elements/new-message/MessageContent.svelte`,
      `talkingcode-frontend/src/lib/components/domain/ChatThread.svelte`,
      `talkingcode-frontend/src/lib/components/ai-elements/response/Response.svelte`.
      Verify: visually denser readability on desktop and mobile; no layout breakage.

- [ ] **Step 3: Refine right-side panel behavior and hierarchy**
      Make panel behavior feel closer to GPT-style activity panel with cleaner title hierarchy,
      better section spacing, and mobile-friendly overlay/drawer behavior.
      File: `talkingcode-frontend/src/lib/components/domain/TurnDetailPanel.svelte`.
      Verify: panel opens/closes reliably, content remains readable, and mobile interaction works.

- [ ] **Step 4: Align strict frontend SSE parser with backend payload shape**
      Update zod schemas to accept backend-emitted keys without dropping events while keeping strict
      validation for unknown structures.
      Files: `talkingcode-frontend/src/lib/services/ChatService.ts`,
      `talkingcode-frontend/src/lib/services/ChatService.spec.ts`.
      Verify: parser handles current backend payloads for `iteration_started`, `tool_call_started`,
      `tool_call_finished`, `assistant_done`.

- [ ] **Step 5: Remove redundant chat action(s) and finalize interaction flow**
      Deprecate or remove panel-open affordances that are no longer primary, keeping one clear
      interaction model centered on the thinking row.
      File: `talkingcode-frontend/src/lib/components/domain/AssistantMessage.svelte`.
      Verify: no duplicated/conflicting CTA for thought details.

- [ ] **Step 6: Verification pass and blueprint update**
      Run frontend checks/tests and backend tests for regression confidence.
      Verify commands:
      - `pnpm --dir talkingcode-frontend check`
      - `pnpm --dir talkingcode-frontend test:unit -- --run`
      - `uv run pytest backend/tests -q`

## Tests

- Frontend unit tests for stream parser compatibility with backend-style SSE payloads
- Frontend type/svelte checks for component prop and interaction wiring
- Backend tests as regression guard (no behavior regressions in agent loop endpoints)

## Verification

1. Start app and open `/chat`.
2. Ask a question that triggers reasoning and tool calls.
3. Click the thinking row in assistant message; right panel opens for the same message.
4. Confirm panel updates while streaming and remains usable after completion.
5. Confirm assistant body text is visibly more legible (inspired by GPT/Claude, not cloned).
6. Confirm mobile panel behavior is usable (overlay/drawer acceptable).
