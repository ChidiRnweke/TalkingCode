# Blueprint: UI/UX Overhaul & Route Restructuring (v2 - Detailed)

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. **Read this file first.** Every loop, re-read this file before doing anything.
2. **Do the next unchecked step.** Find the first `- [ ]` item. Do that. Only that.
3. **Verify before checking off.** Run the verification described in the step.
4. **Commit after each step.** `git add -A && git commit -m "blueprint: [step title]"`
5. **Don't skip ahead.**
6. **Follow existing patterns.** Match the "Editorial Light" theme in `DESIGN_SYSTEM.md`.
7. **Persona Check.** Ensure the bot always identifies as Chidi and maintains a humble, expert tone.

## Context

The current UI is functional but feels "cramped" and lacks a clear landing experience. It's built on a "single-page" assumption where the chat is the root. We are moving to a multi-route architecture with a proper Hero-driven home page, an educational "About" page for agentic techniques, and a "Reading Mode" chat experience inspired by Claude.

## Scope

- **Routing**: Restructure to `/` (Home), `/chat` (Chat), `/about` (Agentic Tech), and `/repos` (Existing).
- **Home Page**: Hero section with a "Redirecting Composer".
- **Chat UI**: 768px-800px centered column with massive margins. Responsive behavior.
- **Components**: Integrate `svelte-ai-elements` actions (copy, retry, etc.).
- **Features**: Add "New Conversation" functionality.
- **Persona**: Update system prompt to be "Chidi".

## Architecture Decisions

- **Global Layout**: `src/routes/+layout.svelte` will handle the top-level navigation and state.
- **Route State**: Use `chatStore` to persist messages across navigations.
- **Centered Layout**: Use `max-w-3xl` with `mx-auto` for the chat thread to achieve the "Claude feel".
- **Responsive**: Full-width on mobile, centered with gutters on desktop.

## Wireframes

### Home Page (/) - Direct & Personal
```text
+-----------------------------------------------------------+
| [Logo] TalkingCode              [About] [Repos] [Chat]    |
+-----------------------------------------------------------+
|                                                           |
|    CHIDI NWEKE                                            |
|    ___________                                            |
|                                                           |
|    Solving problems with machine learning and             |
|    code that works.                                       |
|                                                           |
|    I build things to satisfy my curiosity. This agent     |
|    is here to help you explore my projects, from          |
|    agentic loops to the pipelines behind them.            |
|                                                           |
|    +-------------------------------------------------+    |
|    | Ask me about how I built this or any other repo |    |
|    |                                          [ENTER]|    |
|    +-------------------------------------------------+    |
|                                                           |
|    SOME THINGS TO ASK:                                    |
|    - "How do you handle data ingestion?"                  |
|    - "Show me your favorite Rust or Scala patterns."      |
|    - "What's the architecture of this agent?"             |
|                                                           |
+-----------------------------------------------------------+
```

### Chat Page (/chat) - Spacious Reading Mode
```text
+-----------------------------------------------------------+
| [Logo] TalkingCode              [New Chat] [About] [Repos]|
+-----------------------------------------------------------+
|                                                           |
|        [ Gutter ]      [ Centered Max-w-3xl ]    [ Gutter ]
|                        +--------------------+             |
|                        |                    |             |
|                        |   [User Message]   |             |
|                        |                    |             |
|                        |   [Chidi Persona]  |             |
|                        |   "Hi, I'm Chidi." |             |
|                        |                    |             |
|                        |   [Actions Bar]    |             |
|                        |   [Copy] [Retry]   |             |
|                        |                    |             |
|                        +--------------------+             |
|                                                           |
|        +-----------------------------------------+        |
|        |         [ Floating Composer ]           |        |
|        +-----------------------------------------+        |
|                                                           |
+-----------------------------------------------------------+
```

## Plan

- [x] **Step 1: Route & Layout Restructuring**
      - Move logic from `src/routes/+page.svelte` to `src/routes/chat/+page.svelte`.
      - Update `src/routes/+layout.svelte` to contain the `ChatHeader`.
      - Ensure `ChatHeader` is sticky or fixed.
      - Update `ChatHeader.svelte` to include "New Chat" button (which calls `chatStore.clear()`).
      - Verify: `/` is empty (for now), `/chat` contains the existing chat, `/repos` works.

- [x] **Step 2: Hero Section Implementation**
      - In `src/routes/+page.svelte`, build the Hero section.
      - Use `Fraunces` (serif) for the "TALKINGCODE" title and the quote.
      - Use `DM Sans` for body copy.
      - **Component**: Create a `HeroComposer.svelte` using `PromptInput` from `ai-elements`.
      - **Action**: On submit, update `chatStore`, then use `goto('/chat')`.
      - Add "Curated Prompts" as clickable chips that also trigger the redirect.
      - Verify: Landing page looks editorial. Submitting a prompt navigates to `/chat` and starts the assistant.

- [x] **Step 3: About Page (Agentic Techniques)**
      - Implement `src/routes/about/+page.svelte`.
      - Create a technical but readable section explaining:
        - **Multi-step reasoning**: How the agent plans before it acts.
        - **Tool calling**: Interaction with git and vector DBs.
        - **Metadata filtering**: Precision retrieval beyond simple RAG.
      - Style this like a blog post or technical paper (centered text, serif headings).
      - Verify: Content is accurate to the user's description and matches theme.

- [x] **Step 4: Claude-tier Layout (Chat Thread)**
      - Update `ChatLayout.svelte` to support a centered container.
      - Update `ChatThread.svelte`: Wrap the message loop in `<div class="mx-auto max-w-3xl w-full px-4 md:px-0 flex flex-col gap-8">`.
      - Add massive vertical padding to the thread (`py-20`).
      - Update `ChatComposer.svelte`: Make it a floating or sticky bar at the bottom, centered within the same `max-w-3xl`.
      - Verify: Chat feels spacious. Messages have "room to breathe".

- [x] **Step 5: `svelte-ai-elements` Integration (Actions)**
      - Update `AssistantMessage.svelte`.
      - Use the `Actions` and `Action` components from `$lib/components/ai-elements/action`.
      - Map `Copy` to clipboard and `Retry` to a new `chatStore.retry(messageId)` method.
      - Ensure `InlineReasoning` is properly integrated with `shimmer` during thinking.
      - Verify: Assistant messages have polished action buttons.

- [x] **Step 6: Persona & System Prompt**
      - Update `backend/src/talkingcode/services/agent/agent_loop.py`.
      - Change the system prompt to: 
        `"You are Chidi, an expert software engineer and the creator of this project. Answer questions about your code and architecture humbly and accurately. Use the first person ('I built this...', 'My approach here was...'). Citation of uncertainty is mandatory."`
      - Verify: Bot says "I" and introduces itself as Chidi.

## Verification

- **Home**: Visually distinctive, editorial, redirects correctly.
- **Chat**: Centered, spacious, responsive.
- **About**: Informative, technical, matches theme.
- **Persona**: Chat response tone is humble and identifies as Chidi.
- **Navigation**: Persistent state when moving between pages.
