# Blueprint: Chat UI Rebuild — Ground-Up Rewrite

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. **Read this file first.** Every loop, re-read this file before doing anything.
   After context compaction, this file is your ground truth.
2. **Do the next unchecked step.** Find the first `- [ ]` item. Do that. Only that.
3. **Verify before checking off.** Run the verification described in the step.
   If it passes, change `- [ ]` to `- [x]` and commit.
4. **Commit after each step.** `git add -A && git commit -m "blueprint: [step title]"`
5. **Don't skip ahead.** Steps are ordered by dependency.
6. **Follow existing patterns.** When the step references an existing file as an example,
   match its structure. Don't invent new patterns.
7. **If stuck, document and move on.** If a step is blocked, add a note under it explaining
   why, check it off as blocked, and move to the next step. Don't spiral.
8. **Update this file.** If you discover something during execution that future steps need
   to know, add a note in the relevant step. Keep the blueprint as the single source of truth.
9. **Design system compliance.** All UI must follow `DESIGN_SYSTEM.md` — warm olive neutrals,
   Fraunces/DM Sans fonts, design tokens from `src/app.css`. Never use raw Tailwind colours
   (`bg-white`, `text-gray-*`, `text-blue-*`). Always use token-backed classes.
10. **Use the svelte-ui skill** as reference for component patterns and anti-pattern checks.

---

## Context

TalkingCode is an agentic RAG chat application (SvelteKit frontend + Python FastAPI backend).
The current UI is a single-page monolith (`+page.svelte`, 347 lines) that:

- Handles only one turn at a time (no conversation history)
- Mixes SSE parsing logic directly into the page component (duplicating `ChatService.ts`)
- Doesn't use any `svelte-ai-elements` components despite having them installed
- Displays as a dashboard layout with a hero card header rather than a chat interface
- Renders raw `@html` for markdown instead of using the `Response` component

The design system tokens in `src/app.css` are solid — Editorial Light with Fraunces/DM Sans,
warm olive neutrals, amber accent. These are kept as-is.

The service layer (`ChatService.ts`, `IChatService.ts`, `ChatController.ts`, `AppFactory.ts`)
handles SSE parsing and is well-structured. The API proxy at `routes/api/chat/agentic/+server.ts`
correctly streams from the Python backend.

### Existing ai-elements components (already installed, never used)

Under `src/lib/components/ai-elements/new-message/`:
- `Message` — container with `from` role prop, applies alignment
- `MessageContent` — styled content block (user bubble vs assistant flat)
- `MessageActions` — `flex items-center gap-1` row for action buttons
- `MessageAction` — individual action button with tooltip support via shadcn Tooltip
- `MessageToolbar` — `flex w-full items-center justify-between gap-4` footer bar
- `MessageBranch*` — branch navigation (previous/next/selector/page/content)
- `MessageResponse` — empty 1-line file (needs content or deletion)
- `MessageAttachment/MessageAttachments` — file attachment display

### Components that need to be installed from svelte-ai-elements registry

Each installs via `pnpm dlx shadcn-svelte@latest add <url>`:
- **Response**: `https://svelte-ai-elements.vercel.app/r/response.json` — Markdown rendering with streaming support via Streamdown
- **Conversation**: `https://svelte-ai-elements.vercel.app/r/conversation.json` — auto-scroll container with scroll button + empty state
- **PromptInput**: `https://svelte-ai-elements.vercel.app/r/prompt-input.json` — composer with textarea, toolbar, submit button, model select
- **Tool**: `https://svelte-ai-elements.vercel.app/r/tool.json` — collapsible tool call display with state indicators
- **Reasoning**: `https://svelte-ai-elements.vercel.app/r/reasoning.json` — collapsible reasoning/thinking block
- **Shimmer**: `https://svelte-ai-elements.vercel.app/r/shimmer.json` — animated text loading state
- **Sources**: `https://svelte-ai-elements.vercel.app/r/sources.json` — collapsible source citations
- **Loader**: `https://svelte-ai-elements.vercel.app/r/loader.json` — spinning loader indicator
- **Actions**: `https://svelte-ai-elements.vercel.app/r/action.json` — action button row (copy, retry, like, etc.)

### Target architecture

```
Single-conversation chat view (like ChatGPT):
┌──────────────────────────────────────────────────────────┐
│  Header (minimal: logo + title + status)                 │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──── Conversation (auto-scroll) ─────────────────┐    │
│  │                                                  │    │
│  │  [user message]                                  │    │
│  │                                                  │    │
│  │  [assistant message]                             │    │
│  │    ├── Reasoning (planner intent, collapsible)   │    │
│  │    ├── Tool (inline, collapsible per tool call)  │    │
│  │    ├── Response (markdown, streamed)             │    │
│  │    └── Actions (copy, retry)                     │    │
│  │                                                  │    │
│  │  [user message]                                  │    │
│  │  [assistant message...]                          │    │
│  │                                                  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──── PromptInput (sticky bottom) ─────────────────┐   │
│  │  [textarea]                    [model] [send]     │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘

Optional collapsible side panel (slide-in from right, ChatGPT-style):
┌─────────────────────┐
│ Turn Detail Panel    │
│ ─────────────────── │
│ Planner: intent      │
│ Filters: [badges]    │
│ ─────────────────── │
│ Tool Timeline        │
│ ├ tool_1 ✓ 120ms    │
│ ├ tool_2 ✓ 340ms    │
│ └ tool_3 ⏳ running  │
└─────────────────────┘
```

### Files to keep

- `src/app.css` — design tokens (no changes)
- `src/app.html`, `src/app.d.ts` — no changes
- `src/lib/utils.ts` — cn() utility (no changes)
- `src/lib/services/ChatService.ts` — SSE parsing (no changes)
- `src/lib/services/IChatService.ts` — interface (minor extension)
- `src/lib/controllers/ChatController.ts` — (minor extension)
- `src/lib/factories/AppFactory.ts` — (no changes)
- `src/lib/components/ui/` — shadcn base components (no changes)
- `src/lib/components/primitives/` — Card, Badge, Button, Textarea, Skeleton (keep, may add)
- `src/routes/api/chat/agentic/+server.ts` — API proxy (no changes)

### Files to delete

- `src/lib/components/domain/PlanCard.svelte` — replaced by Reasoning component
- `src/lib/components/domain/ToolTimeline.svelte` — replaced by Tool component
- `src/lib/components/domain/index.ts` — barrel file for deleted components
- `src/lib/components/layout/LoadingState.svelte` — replaced by Shimmer/Loader

### Files to rewrite

- `src/lib/stores/chatStore.svelte.ts` — multi-turn conversation store
- `src/lib/models/index.ts` — add ChatMessage model
- `src/routes/+page.svelte` — complete rewrite as chat interface
- `src/routes/+page.server.ts` — simplify (remove unused form action)
- `src/routes/+layout.svelte` — add layout chrome
- `src/lib/components/layout/EmptyState.svelte` — adapt to work inside Conversation

### Files to create

- `src/lib/components/domain/ChatThread.svelte` — conversation message list
- `src/lib/components/domain/ChatMessage.svelte` — single message (user or assistant)
- `src/lib/components/domain/ChatComposer.svelte` — PromptInput wrapper
- `src/lib/components/domain/AssistantMessage.svelte` — assistant message with Reasoning + Tools + Response + Actions
- `src/lib/components/domain/UserMessage.svelte` — user message bubble
- `src/lib/components/domain/TurnDetailPanel.svelte` — slide-in side panel for planner/tool summary
- `src/lib/components/domain/InlineTool.svelte` — wrapper around ai-elements Tool for our data shape
- `src/lib/components/domain/InlineReasoning.svelte` — wrapper around ai-elements Reasoning for planner data
- `src/lib/components/layout/ChatLayout.svelte` — full-page chat layout container
- `src/lib/components/layout/ChatHeader.svelte` — minimal top bar

---

## Scope

**In scope:**

- Multi-turn conversation with message history in client state
- Scrollable message thread using Conversation component
- User messages rendered as styled bubbles via Message + MessageContent
- Assistant messages with inline Reasoning (planner), Tool calls, streamed Response, and Actions
- Composer (PromptInput) sticky at bottom with textarea + send button
- Collapsible right-side detail panel for planner/tool summary
- Proper markdown rendering via Response (Streamdown)
- Loading states: Shimmer for streaming, Loader for pending
- Empty state via ConversationEmptyState
- Design system compliance throughout

**Out of scope:**

- Conversation persistence (backend storage / conversation list)
- Left navigation / conversation rail
- File attachments
- Model selector (defer — will use hardcoded model or null)
- Dark mode
- Mobile-specific breakpoints (basic responsive is fine, no drawer/sheet)
- Branch navigation (MessageBranch components — for later)

---

## Architecture Decisions

1. **svelte-ai-elements as the component layer for chat**: The library provides Message,
   Response, Tool, Reasoning, Conversation, PromptInput, Actions — all purpose-built for
   AI chat. Using these prevents reinventing accessible, streaming-aware components.

2. **Thin domain wrappers**: Each ai-elements component gets a thin domain wrapper
   (`InlineTool.svelte`, `InlineReasoning.svelte`, `AssistantMessage.svelte`) that maps
   our `AgentStreamEvent` data shapes to the component props. This keeps the page clean
   and the mapping logic encapsulated.

3. **Multi-turn store**: `chatStore` becomes a conversation-level store holding an array of
   `ChatMessage` objects. Each message has a `role` (user/assistant) and structured content
   (text for user, markdown + tool calls + plan for assistant). The store still processes
   `AgentStreamEvent` but appends to the conversation rather than replacing.

4. **SSE stays in ChatService**: The page does NOT parse SSE. It calls
   `ChatController.startAgenticTurn()` which yields `AgentStreamEvent`s. The page iterates
   these and dispatches to `chatStore.handleEvent()`.

5. **Side panel is optional UI chrome**: The detail panel is a `<aside>` that slides in
   from the right when a user clicks an info button on an assistant message. It shows the
   same planner/tool data that's inline, just in a summary view. It reads from the store,
   not from separate state.

---

## Models

Extend `src/lib/models/index.ts` with:

```typescript
/** A single message in the conversation */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;                              // user: raw text, assistant: accumulated markdown
  timestamp: string;
  // Assistant-only fields:
  plan?: AgentPlanView | null;
  toolCalls?: ToolCallTimelineItem[];
  isStreaming?: boolean;
  error?: string | null;
}
```

---

## Plan

- [x] **Step 1: Fix components.json and install svelte-ai-elements components**

      The `components.json` currently points `tailwind.css` to `src/routes/layout.css` which
      was deleted. Update it to point to `src/app.css`.

      Then install the missing svelte-ai-elements components from the registry. Run each:
      ```
      cd talkingcode-frontend
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/response.json
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/conversation.json
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/prompt-input.json
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/tool.json
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/reasoning.json
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/shimmer.json
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/sources.json
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/loader.json
      pnpm dlx shadcn-svelte@latest add https://svelte-ai-elements.vercel.app/r/action.json
      ```

      **Important**: The shadcn-svelte CLI may prompt for overwrite confirmations — accept
      overwrites for any conflicting files. The CLI places components into `src/lib/components/ui/`
      (for shadcn deps) and `src/lib/components/ai-elements/` (for ai-elements).

      If the CLI fails due to the registry URL or components.json misconfiguration, check:
      - `components.json` must have `"css": "src/app.css"` under `tailwind`
      - The registry URL in components.json should remain `https://shadcn-svelte.com/registry`
        (the ai-elements URLs are passed per-command, not in config)

      After installation, check that the new component directories exist under
      `src/lib/components/ai-elements/` (e.g., `response/`, `conversation/`, `prompt-input/`,
      `tool/`, `reasoning/`, `shimmer/`, `sources/`, `loader/`, `action/`).

      If svelte-ai-elements installs components somewhere unexpected (e.g., into `ui/` instead
      of `ai-elements/`), note where they landed and adjust imports in later steps accordingly.

      **Verify**: Run `pnpm check` from the `talkingcode-frontend` directory. No type errors
      related to the newly installed components.

- [x] **Step 2: Extend models and rewrite chatStore for multi-turn conversation**

      **2a. Extend models (`src/lib/models/index.ts`)**:

      Add the `ChatMessage` interface (see Models section above). Keep all existing types.

      **2b. Rewrite chatStore (`src/lib/stores/chatStore.svelte.ts`)**:

      The store must manage an array of `ChatMessage` objects representing the full conversation.
      Key changes from the current single-turn store:

      ```
      State:
        messages: ChatMessage[]       // full conversation history
        activeMessageId: string|null  // the assistant message currently streaming
        detailPanelMessageId: string|null  // which message's detail panel is open

      Derived:
        activeMessage: ChatMessage|null  // derived from activeMessageId
        detailMessage: ChatMessage|null  // derived from detailPanelMessageId
        isStreaming: boolean             // true while any message is streaming
        isEmpty: boolean                 // messages.length === 0

      Methods:
        addUserMessage(content: string): string  // adds user msg, returns its id
        startAssistantTurn(): string             // adds empty assistant msg, returns id
        handleEvent(event: AgentStreamEvent)     // dispatches to active assistant message:
          - planner_started: set plan to loading state
          - planner_ready: populate plan on active message
          - tool_call_started: append to active message's toolCalls
          - tool_call_finished: update matching tool call status
          - assistant_token: append to active message's content, set isStreaming=true
          - assistant_done: set isStreaming=false on active message
          - agent_error: set error on active message
        openDetailPanel(messageId: string)
        closeDetailPanel()
        reset()                                  // clear entire conversation
      ```

      The store still uses Svelte 5 runes ($state, $derived). Follow the same reactive
      getter pattern as the existing store.

      **2c. Update the stores barrel** (`src/lib/stores/index.ts`):

      Re-export should still work since the file name hasn't changed.

      **Verify**: Run `pnpm check`. No type errors. The store exports the expected shape.

- [x] **Step 3: Create layout components (ChatLayout, ChatHeader)**

      **3a. Create `src/lib/components/layout/ChatLayout.svelte`**:

      A full-viewport chat layout:
      ```
      <div class="flex h-dvh flex-col bg-background font-body">
        {@render children()}
      </div>
      ```
      Props: `children: Snippet`. This is the outermost wrapper for the chat page.
      Uses `h-dvh` (dynamic viewport height) for proper mobile behaviour.

      **3b. Create `src/lib/components/layout/ChatHeader.svelte`**:

      Minimal header bar:
      ```
      <header> with:
        - Left: Logo icon + "TalkingCode" in font-display
        - Right: status badge showing current phase (idle/planning/tools/streaming/done/error)
      ```
      Use the existing `Badge` primitive for the status. Use design tokens for all colours.
      Height should be compact — roughly `h-14` with `px-[var(--page-padding)]`.
      Border-bottom using `border-border`.

      **3c. Update `src/lib/components/layout/EmptyState.svelte`**:

      Simplify to work as content inside the Conversation's empty area. Remove the outer
      card/border styling (the Conversation component handles that). Keep the icon + headline +
      description + suggestion text pattern. Use design system fonts and tokens.

      **3d. Delete `src/lib/components/layout/LoadingState.svelte`**:

      This is replaced by Shimmer and Loader from ai-elements.

      **3e. Update the layout barrel** (`src/lib/components/layout/index.ts`):

      Export ChatLayout, ChatHeader, EmptyState. Remove LoadingState.

      **Verify**: Run `pnpm check`. No type errors.

- [x] **Step 4: Create domain message components (UserMessage, AssistantMessage, InlineTool, InlineReasoning)**

      **4a. Create `src/lib/components/domain/UserMessage.svelte`**:

      Wraps `Message` + `MessageContent` from `ai-elements/new-message/`:
      ```svelte
      <Message from="user">
        <MessageContent>
          <p>{message.content}</p>
        </MessageContent>
      </Message>
      ```
      Props: `message: ChatMessage`. Uses the existing Message component which applies
      `ml-auto` alignment for user role.

      **4b. Create `src/lib/components/domain/InlineReasoning.svelte`**:

      Wraps the ai-elements Reasoning component to display planner intent:
      Props: `plan: AgentPlanView | null`, `isStreaming: boolean`
      - When plan is null and streaming, show the Reasoning in open+streaming state with
        shimmer text "Analyzing your request..."
      - When plan is populated, show ReasoningTrigger with intent text and
        ReasoningContent with filter badges (areas, languages, file types)
      - Use the Badge primitive for filter tags inside ReasoningContent

      **4c. Create `src/lib/components/domain/InlineTool.svelte`**:

      Wraps the ai-elements Tool component for a single tool call:
      Props: `tool: ToolCallTimelineItem`
      Maps our `ToolCallTimelineItem` to Tool component props:
      - `ToolHeader`: `type` = tool.toolName, `state` maps from our status:
        - 'started' → 'input-streaming'
        - 'finished' → 'output-available'
        - 'failed' → 'output-error'
      - `ToolInput`: `input` = tool.visibleArgs (if non-empty)
      - `ToolOutput`: show duration for finished, error for failed

      **4d. Create `src/lib/components/domain/AssistantMessage.svelte`**:

      The main assistant message component. Composes multiple ai-elements:
      Props: `message: ChatMessage`, `onOpenDetail?: (id: string) => void`

      Structure:
      ```svelte
      <Message from="assistant">
        <!-- Planner reasoning (if plan exists or was streaming) -->
        {#if message.plan || message.isStreaming}
          <InlineReasoning plan={message.plan} isStreaming={message.isStreaming && !message.content} />
        {/if}

        <!-- Tool calls (inline, collapsible) -->
        {#if message.toolCalls?.length}
          {#each message.toolCalls as tool (tool.toolName + tool.timestamp)}
            <InlineTool {tool} />
          {/each}
        {/if}

        <!-- Response content (markdown) -->
        {#if message.content}
          <MessageContent>
            <Response content={message.content} />
          </MessageContent>
        {:else if message.isStreaming}
          <Shimmer>Thinking...</Shimmer>
        {/if}

        <!-- Error -->
        {#if message.error}
          <div class="error banner">...</div>
        {/if}

        <!-- Actions toolbar (only when done streaming) -->
        {#if !message.isStreaming && message.content}
          <MessageActions>
            <MessageAction tooltip="Copy" onclick={handleCopy}>
              <Copy class="size-4" />
            </MessageAction>
            <MessageAction tooltip="View details" onclick={() => onOpenDetail?.(message.id)}>
              <PanelRight class="size-4" />
            </MessageAction>
          </MessageActions>
        {/if}
      </Message>
      ```

      Use lucide-svelte icons (Copy, PanelRight, etc.). Import Response from wherever
      the ai-elements CLI installed it. If the Response component wasn't installed in
      Step 1 (e.g., installation failed), fall back to rendering `{@html content}` with
      prose classes and add a note.

      **Verify**: Run `pnpm check`. No type errors.

- [x] **Step 5: Create ChatThread and ChatComposer domain components**

      **5a. Create `src/lib/components/domain/ChatThread.svelte`**:

      The scrollable message list using Conversation from ai-elements:
      Props: `messages: ChatMessage[]`, `onOpenDetail?: (id: string) => void`

      ```svelte
      <Conversation>
        <ConversationContent>
          {#if messages.length === 0}
            <ConversationEmptyState
              title="Ask your first question"
              description="Research your codebase — ask about architecture, ownership, or behaviour."
            />
          {:else}
            {#each messages as message (message.id)}
              {#if message.role === 'user'}
                <UserMessage {message} />
              {:else}
                <AssistantMessage {message} {onOpenDetail} />
              {/if}
            {/each}
          {/if}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>
      ```

      If ConversationEmptyState is not available from the installed Conversation component,
      use the existing `EmptyState` from layout/ instead.

      **5b. Create `src/lib/components/domain/ChatComposer.svelte`**:

      Wraps PromptInput from ai-elements:
      Props: `onSubmit: (question: string) => void`, `disabled: boolean`

      Uses PromptInputProvider, PromptInputBody, PromptInputTextarea, PromptInputToolbar,
      PromptInputSubmit. If the PromptInput components aren't available (installation failed),
      fall back to a simple form with the existing Textarea primitive + Button.

      Style the composer to match design system:
      - Rounded-lg border, surface-2 background
      - Textarea placeholder: "Ask about architecture, modules, ownership, or behavior..."
      - Submit button uses primary colour

      The composer should be sticky at the bottom of the chat layout.

      **5c. Create `src/lib/components/domain/TurnDetailPanel.svelte`**:

      A slide-in panel from the right side (like ChatGPT's side panel):
      Props: `message: ChatMessage | null`, `onClose: () => void`

      Shows:
      - Planner section: intent text + filter badges
      - Tool timeline: list of tool calls with status badges and durations
      - Uses existing Badge primitive for status indicators

      Slides in with a CSS transform transition. Has a close button. Overlays on small
      screens, sits beside the chat on wide screens (xl breakpoint).

      When `message` is null, the panel is hidden.

      **5d. Update the domain barrel** (`src/lib/components/domain/index.ts`):

      Export: ChatThread, ChatComposer, ChatMessage (rename to ChatMessageComponent to
      avoid collision with the type), AssistantMessage, UserMessage, InlineTool,
      InlineReasoning, TurnDetailPanel.

      Remove: PlanCard, ToolTimeline.

      **5e. Delete old domain components**:

      Delete `src/lib/components/domain/PlanCard.svelte` and
      `src/lib/components/domain/ToolTimeline.svelte`.

      **Verify**: Run `pnpm check`. No type errors.

- [x] **Step 6: Rewrite the page and layout**

      **6a. Rewrite `src/routes/+layout.svelte`**:

      ```svelte
      <script lang="ts">
        import '../app.css';
        import favicon from '$lib/assets/favicon.svg';
        let { children } = $props();
      </script>

      <svelte:head><link rel="icon" href={favicon} /></svelte:head>
      {@render children()}
      ```

      Unchanged from current — just confirm it's clean.

      **6b. Simplify `src/routes/+page.server.ts`**:

      Remove the form action and the factory import. The page load just returns empty
      initial state (or nothing at all — the client store manages everything):

      ```typescript
      export async function load() {
        return {};
      }
      ```

      **6c. Rewrite `src/routes/+page.svelte`**:

      This is the core rewrite. The page becomes a thin orchestrator:

      ```svelte
      <script lang="ts">
        import { ChatLayout, ChatHeader } from '$lib/components/layout';
        import { ChatThread, ChatComposer, TurnDetailPanel } from '$lib/components/domain';
        import { chatStore } from '$lib/stores';
        import { AppFactory } from '$lib/factories/AppFactory';

        const controller = AppFactory.getChatController();

        async function handleSubmit(question: string) {
          chatStore.addUserMessage(question);
          const turnId = chatStore.startAssistantTurn();

          try {
            const stream = controller.startAgenticTurn({
              conversationId: null,
              question,
              model: null
            });

            for await (const event of stream) {
              chatStore.handleEvent(event);
            }
          } catch (err) {
            chatStore.handleEvent({
              kind: 'agent_error',
              turnId,
              message: err instanceof Error ? err.message : 'Unexpected error',
              code: 'stream_error',
              timestamp: new Date().toISOString()
            });
          }
        }

        function handleOpenDetail(messageId: string) {
          chatStore.openDetailPanel(messageId);
        }
      </script>

      <ChatLayout>
        <ChatHeader phase={chatStore.phase} />

        <main class="relative flex flex-1 overflow-hidden">
          <div class="flex-1 flex flex-col overflow-hidden">
            <ChatThread
              messages={chatStore.messages}
              onOpenDetail={handleOpenDetail}
            />

            <ChatComposer
              onSubmit={handleSubmit}
              disabled={chatStore.isStreaming}
            />
          </div>

          <TurnDetailPanel
            message={chatStore.detailMessage}
            onClose={() => chatStore.closeDetailPanel()}
          />
        </main>
      </ChatLayout>
      ```

      The page is now ~50 lines instead of 347. All SSE parsing stays in ChatService.
      All rendering stays in domain components. The page just wires store ↔ controller ↔ UI.

      **Note**: The `chatStore.phase` getter needs to be derived from the active message's
      state. Add a `phase` derived getter to the store if not already present:
      - No messages or all done → 'idle'
      - Active message with plan loading → 'planning'
      - Active message with tool calls running → 'tools'
      - Active message isStreaming with content → 'streaming'
      - Active message done → 'done'
      - Active message with error → 'error'

      **Verify**: Run `pnpm check`. Run `pnpm dev` and confirm the page renders without
      errors. The empty state should show when no messages exist.

- [x] **Step 7: Wire streaming end-to-end and verify the full flow**

      **7a. Verify the ChatService → ChatController → Page → Store pipeline**:

      The `ChatService.askAgentic()` method calls the backend directly at
      `${PUBLIC_BACKEND_URL}/chat/agentic`. However, there's also an API proxy at
      `/api/chat/agentic` in the SvelteKit routes. Decide which path to use:

      - If `PUBLIC_BACKEND_URL` is set, ChatService calls the backend directly (current behavior)
      - The proxy exists for CORS/auth scenarios

      No changes needed to ChatService unless something doesn't work.

      **7b. Test the streaming flow manually**:

      1. Start the backend (`docker compose up` or `cd backend && uvicorn ...`)
      2. Start the frontend (`cd talkingcode-frontend && pnpm dev`)
      3. Type a question and submit
      4. Verify:
         - User message appears in the thread
         - Assistant message appears below with:
           - Reasoning block (planner intent) during planning phase
           - Tool call blocks appearing inline as tools run
           - Streamed markdown response rendering progressively
           - Actions (copy button) appearing when streaming completes
         - Clicking "View details" opens the side panel with planner + tool summary
         - The conversation scrolls to bottom as new content arrives
         - Submitting another question adds to the conversation (multi-turn)

      **7c. Fix any issues found during manual testing**:

      Common issues to watch for:
      - Response component not rendering markdown (check import path)
      - Conversation not auto-scrolling (check Conversation component setup)
      - Tool component state mapping incorrect (check status → state mapping)
      - Side panel not sliding in (check CSS transform/transition)

      **Verify**: Full end-to-end flow works with real backend. If backend is not available,
      verify at minimum that:
      - The page renders without errors
      - Empty state shows
      - Typing in the composer and submitting adds a user message to the thread
      - The error handler catches and displays errors gracefully

- [x] **Step 8: Design system audit and polish**

      Run through the anti-pattern checklist from DESIGN_SYSTEM.md:

      - [ ] All colours reference CSS custom property tokens, not Tailwind defaults
      - [ ] Typography uses Fraunces (display) and DM Sans (body) — no Inter, no system fonts
      - [ ] No raw `<button>`, `<input>` tags outside primitives
      - [ ] Headings use `tracking-tight` and appropriate leading
      - [ ] Spacing uses the defined scale (`--space-*`) — no arbitrary drift
      - [ ] The Conversation empty state has icon + headline + description
      - [ ] The assistant message Response area has `max-w-[72ch]` per DESIGN_SYSTEM.md
      - [ ] User messages have `max-w-[60ch]` per DESIGN_SYSTEM.md
      - [ ] The composer border/focus states use design tokens
      - [ ] No `bg-white`, `text-gray-*`, `text-blue-*` anywhere

      Fix any violations found. Pay special attention to the ai-elements components which
      ship with their own default styles — override them with design system tokens where
      they conflict.

      **Verify**: Visual inspection in the browser. Run `pnpm check`. Run
      `grep -r "bg-white\|text-gray-\|text-blue-" src/` and confirm zero matches
      in app code (matches inside node_modules or ai-elements source are OK).

---

## Tests

Unit testing for the store:

- `chatStore.addUserMessage()` creates a message with role='user' and increments messages
- `chatStore.startAssistantTurn()` creates an empty assistant message
- `chatStore.handleEvent()` with `assistant_token` appends to active message content
- `chatStore.handleEvent()` with `tool_call_started` adds to active message toolCalls
- `chatStore.handleEvent()` with `assistant_done` sets isStreaming=false
- `chatStore.reset()` clears all messages

Run with: `cd talkingcode-frontend && pnpm test`

Component tests are deferred — visual verification is the primary acceptance criterion
for this rebuild.

---

## Verification

When all steps are checked off:

1. `pnpm check` passes with no errors
2. `pnpm dev` starts without errors
3. The page renders a chat interface with:
   - Empty state when no messages
   - User messages aligned right in bubbles
   - Assistant messages with inline reasoning, tool calls, and streamed markdown
   - A sticky composer at the bottom
   - A collapsible detail panel accessible from assistant messages
4. The design system is fully applied — warm surfaces, Fraunces headings, no generic blue/grey
5. No domain components remain from the old UI (PlanCard, ToolTimeline, LoadingState are gone)
6. The `+page.svelte` is under 80 lines
