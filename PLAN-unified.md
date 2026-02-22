# Blueprint: TalkingCode V1 — Complete Implementation

## Executor Instructions

You are executing this blueprint. Follow these rules:

1. **Read this file first.** Every loop, re-read this file before doing anything.
   After context compaction, this file is your ground truth.
2. **Do the next unchecked step.** Find the first `- [ ]` item. Do that. Only that.
3. **Verify before checking off.** Run the verification described in the step.
   If it passes, change `- [ ]` to `- [x]` and commit.
4. **Commit after each step.** `git add -A && git commit -m "blueprint: Step X.Y — [title]"`
5. **Don't skip ahead.** Steps are ordered by dependency.
6. **Follow existing patterns.** When the step references an existing file as an example,
   match its structure exactly. Don't invent new patterns.
7. **If stuck, document and move on.** If a step is blocked, add a note under it explaining
   why, check it off as blocked, and move to the next step. Don't spiral.
8. **Update this file.** If you discover something during execution that future steps need
   to know, add a note in the relevant step. Keep the blueprint as the single source of truth.
9. **Design system.** All frontend UI must follow `DESIGN_SYSTEM.md`. Never use `bg-white`,
   `text-gray-*`, `text-blue-*`. Always use token-backed classes (`bg-background`,
   `text-foreground`, `text-muted-foreground`, `border-border`, etc.).
10. **Backend patterns.** Follow `python-swe` skill strictly:
    - `@dataclass(slots=True)` for services/repositories/controllers
    - `@dataclass(slots=True, frozen=True)` for domain models and inputs
    - Protocol interfaces for service contracts
    - Module-level `logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)`
    - Repositories return domain models, never ORM types
    - Services never import each other — dependencies injected via constructor
    - Errors use `talkingcode.errors` hierarchy (`NotFoundError`, `InfraError`, etc.)

---

## Context

TalkingCode is a BFF monorepo (SvelteKit frontend + Python FastAPI backend) for conversational
code understanding over a user's GitHub repositories. It is both:
- A **general-purpose tool** anyone can deploy to chat with their own codebase
- A **personal instance** for Chidi Nweke at https://chat.chidinweke.be/

The chat system is agentic-first: planner service analyses the question, tool-calling loop
executes retrieval, and the response streams via SSE with whitebox events (planner_started,
planner_ready, tool_call_started, tool_call_finished, assistant_token, assistant_done,
agent_error). The non-agentic path is deprecated.

### What Already Exists

**Backend (located at `backend/src/talkingcode/`):**
- `config.py` — `Settings` (pydantic_settings) + `AppConfig` (frozen dataclass with `from_env()`)
  - Already has: `github_token`, `openai_api_key`, `embedding_model`, `embedding_dimensions`
- `errors.py` — `AppError > InputError, NotFoundError, InfraError, UnauthorisedError`
- `enums.py` — `Area`, `FileType`, `IngestionStatus`, `TurnStatus`, `ToolCallStatus`, `WhiteboxEventKind`
- `models/orm.py` — Full ORM: `Repository`, `Document`, `DocumentChunk`, `ChunkEmbedding`, `IngestionRun`, `ConversationTurn`, `ToolCallTimeline`
- `domain/models.py` — All chat domain dataclasses (frozen): `AgentTurnInput`, `PlannerInput`, `PlannerOutput`, `RetrievalFilters`, etc.
- `repository/database.py` — `get_engine()`, `get_session()`, `init_db()`
- `repository/document_repository.py` — `DocumentRepository` with `search_chunks`, `save_document`, `save_chunk`, `save_chunk_embedding`
- `repository/conversation_repository.py` — `ConversationRepository` with `create_turn`, `complete_turn`, `get_turn`, `_to_domain()`
- `services/planner/planner_service.py` — `IPlannerService` Protocol + `PlannerService` with OpenRouter
- `services/classification/document_classifier.py` — `DocumentClassifier` with OpenAI
- `services/tools/retriever_tool.py` — `RetrieverTool`
- `services/tools/tool_registry.py` — `ToolRegistry`
- `services/agent/agent_loop.py` — `AgentLoopService` (async generator streaming)
- `services/agent/timeline_repository.py` — `TimelineRepository`
- `controllers/chat_controller.py` — `ChatController` with `start_agentic_turn()` and `get_timeline()`
- `routes/chat_routes.py` — `POST /chat/agentic` (SSE), `GET /chat/timeline`
- `dependencies.py` — `get_config`, `get_db_session`, `get_factory`, `FactoryDep`
- `factory.py` — `AppFactory` with `get_*` methods for all chat services
- `app.py` — `create_app()` with CORS, error handlers, health endpoint, chat router

**Frontend (located at `talkingcode-frontend/src/`):**
- `app.css` — Full design tokens (Editorial Light: Fraunces/DM Sans, warm olive neutrals, amber accent, shadcn mapping)
- `lib/models/index.ts` — Types: `ChatMessage`, `AgentStreamEvent` union, `AgentPlanView`, `ToolCallTimelineItem`, etc.
- `lib/services/IChatService.ts` — `IChatService` interface (`askAgentic`, `getToolTimeline`)
- `lib/services/ChatService.ts` — SSE parsing implementation
- `lib/controllers/ChatController.ts` — Thin orchestrator wrapping `IChatService`
- `lib/factories/AppFactory.ts` — Static `getChatController()` method
- `lib/stores/chatStore.svelte.ts` — Multi-turn reactive store (`messages`, `handleEvent()`, `addUserMessage()`, `startAssistantTurn()`)
- `lib/components/ai-elements/` — Installed svelte-ai-elements:
  - `new-message/` — Message, MessageContent, MessageActions, MessageAction, MessageToolbar, MessageResponse, MessageBranch*, MessageAttachment*
  - `response/` — Response (streamdown markdown)
  - `conversation/` — Conversation, ConversationContent, ConversationEmptyState, ConversationScrollButton
  - `prompt-input/` — PromptInput, PromptInputProvider, PromptInputBody, PromptInputTextarea, PromptInputToolbar, PromptInputSubmit, PromptInputModelSelect, PromptInputModelSelectTrigger, PromptInputModelSelectContent, PromptInputModelSelectItem, PromptInputModelSelectValue
  - `tool/` — Tool, ToolHeader, ToolInput, ToolOutput
  - `reasoning/` — Reasoning, ReasoningTrigger, ReasoningContent
  - `shimmer/` — Shimmer
  - `sources/` — Sources
  - `loader/` — Loader
  - `action/` — Action
  - `code/` — Code, CopyButton
  - `copy-button/` — CopyButton
- `lib/components/domain/` — AssistantMessage, UserMessage, InlineTool, InlineReasoning, ChatThread, ChatComposer, TurnDetailPanel
- `lib/components/layout/` — ChatLayout, ChatHeader, EmptyState
- `routes/+page.svelte` — 60-line orchestrator wiring store + controller
- `routes/+page.server.ts` — Empty load function
- `routes/+layout.svelte` — Imports app.css, renders children
- `routes/api/chat/agentic/+server.ts` — API proxy route

### What's Missing

**Backend:**
- No ingestion pipeline (GitHub fetcher, chunker, embedder, orchestrator)
- No repo management repository/controller/routes
- No Alembic migration infrastructure

**Frontend:**
- ChatComposer uses raw `<textarea>` + `<Button>`, NOT ai-elements PromptInput
- No model selector (PromptInputModelSelect components exist but are unused)
- No personal branding — empty state is generic, header says just "TalkingCode"
- No suggestion prompts in empty state
- No repo management page (`/repos`)
- No navigation between pages
- No ingestion status UI

---

## Scope

**In scope:**

Phase A — Frontend quick wins:
- Personal branding in header and empty state
- Suggestion prompts in empty state
- Replace ChatComposer with ai-elements PromptInput + ModelSelect
- Add model selector

Phase B — Backend ingestion pipeline:
- Alembic migration infrastructure
- Domain models for ingestion
- RepoRepository for repository + ingestion run management
- GitHub file fetcher service
- Document chunker service
- Embedding generator service
- Ingestion orchestrator service
- Ingestion controller
- Repo management + ingestion routes
- Wire into factory

Phase C — Frontend repo management:
- Navigation bar
- Repo management page with register + ingest + history
- Frontend service + types for repo API

Phase D — Integration & polish:
- Design system audit
- End-to-end verification

**Out of scope:**
- Conversation persistence across sessions (localStorage or backend)
- Conversation list/rail
- Dark mode
- Token/usage tracking
- Background job scheduling (APScheduler/Celery)
- About / Host-it-yourself pages
- File attachments
- Branch navigation (MessageBranch components)
- Confidence scoring
- Live GitHub fallback in file-details tool

---

## Architecture Decisions

1. **Backend service pattern**: Every new service gets a Protocol interface (e.g. `IGitHubFetcher`) and a `@dataclass(slots=True)` implementation. Dependencies injected via constructor fields. Follow `PlannerService` in `backend/src/talkingcode/services/planner/planner_service.py` as the canonical example.

2. **Backend repository pattern**: New repositories are `@dataclass(slots=True)` with `session: AsyncSession`. They have a private `_to_domain()` method to convert ORM → domain models. Follow `ConversationRepository` in `backend/src/talkingcode/repository/conversation_repository.py` as the canonical example.

3. **Backend route pattern**: FastAPI `APIRouter()`, routes receive `factory: AppFactory = Depends(get_factory)` via the existing dependency in `backend/src/talkingcode/dependencies.py`. Route functions create controllers from the factory and delegate. Follow `chat_routes.py` in `backend/src/talkingcode/routes/chat_routes.py` as the canonical example.

4. **Backend error handling**: Use `NotFoundError(resource="...")` from `talkingcode.errors`. The global error handler in `app.py` maps these to HTTP responses. Never put HTTP status codes in domain errors.

5. **Frontend component pattern**: Domain components live in `talkingcode-frontend/src/lib/components/domain/`. They use `$props()` with a TypeScript `Props` interface. Follow `AssistantMessage.svelte` as the canonical example for composing ai-elements components.

6. **Frontend service pattern**: New services get an interface (e.g. `IRepoService.ts`) and an implementation (`RepoService.ts`). Follow `IChatService.ts` / `ChatService.ts` as the canonical example. Services are wired through `AppFactory.ts`.

7. **Frontend API proxy pattern**: SvelteKit API routes proxy to the backend. Follow `routes/api/chat/agentic/+server.ts` as the canonical example. The backend URL comes from environment variables.

8. **PromptInput ai-elements**: The `PromptInput` component is a `<form>` wrapper. Its `onSubmit` callback receives `{ text: string, files: FileUIPart[] }`. The `PromptInputTextarea` uses `name="message"` and handles Enter/Shift+Enter. The `PromptInputModelSelect` wraps shadcn `Select.Root`.

---

## Plan

### Phase A: Frontend Quick Wins

- [x] **Step A.1: Personalize the empty state with suggestion prompts**

      **Files to modify:**
      - `talkingcode-frontend/src/lib/components/layout/EmptyState.svelte`
      - `talkingcode-frontend/src/lib/components/domain/ChatThread.svelte`
      - `talkingcode-frontend/src/routes/+page.svelte`

      **What to do:**

      1. Open `talkingcode-frontend/src/lib/components/layout/EmptyState.svelte`. Currently it has
         props `{ title, description, icon }` and renders a generic message. Add two new props:

         ```typescript
         interface Props {
           title?: string;
           description?: string;
           icon?: typeof Component;
           suggestions?: string[];
           onSuggestionClick?: (suggestion: string) => void;
         }
         ```

      2. Below the description paragraph, render the suggestion pills:

         ```svelte
         {#if suggestions && suggestions.length > 0}
           <div class="mt-6 flex flex-wrap justify-center gap-2">
             {#each suggestions as suggestion}
               <button
                 type="button"
                 onclick={() => onSuggestionClick?.(suggestion)}
                 class="rounded-[var(--radius-full)] border border-border bg-[hsl(var(--color-surface-2))] px-4 py-2 text-sm text-foreground transition-colors hover:bg-[hsl(var(--color-surface-3))]"
               >
                 {suggestion}
               </button>
             {/each}
           </div>
         {/if}
         ```

      3. Open `talkingcode-frontend/src/lib/components/domain/ChatThread.svelte`. Currently it
         passes content to `ConversationEmptyState`. Add an `onSuggestionClick` prop to ChatThread:

         ```typescript
         interface Props {
           messages: ChatMessage[];
           onOpenDetail?: (messageId: string) => void;
           onSuggestionClick?: (suggestion: string) => void;
         }
         ```

         Inside the `ConversationEmptyState` slot, render the `EmptyState` component with
         suggestions and pass through the callback:

         ```svelte
         <ConversationEmptyState>
           <EmptyState
             title="Chat with Chidi's code"
             description="Ask questions about architecture, modules, ownership, or behavior across all indexed repositories."
             suggestions={[
               "What projects has Chidi built in Python?",
               "Walk me through the architecture of this repo",
               "What testing patterns are used across the codebase?",
               "Show me the most complex modules and explain them",
             ]}
             onSuggestionClick={onSuggestionClick}
           />
         </ConversationEmptyState>
         ```

         Make sure to import `EmptyState` from `$lib/components/layout`.

      4. Open `talkingcode-frontend/src/routes/+page.svelte`. Pass a `onSuggestionClick` prop
         to `ChatThread` that calls `handleSubmit`:

         ```svelte
         <ChatThread
           messages={chatStore.messages}
           onOpenDetail={handleOpenDetail}
           onSuggestionClick={handleSubmit}
         />
         ```

       **Verify:** Run `cd talkingcode-frontend && pnpm check`. Open the app in browser. The empty
       state shows "Chat with Chidi's code" title, a description, and 4 clickable suggestion pills.
       Clicking a pill submits it as a question and starts a chat turn.

      Note: Implemented and wired suggestion pills/callback. `pnpm check` currently fails due
      pre-existing type errors in `InlineReasoning.svelte` and `TurnDetailPanel.svelte` badge
      props (`size`/variant values), unrelated to this step.

---

- [x] **Step A.2: Update ChatHeader with personal branding and navigation stub**

      **Files to modify:**
      - `talkingcode-frontend/src/lib/components/layout/ChatHeader.svelte`

      **What to do:**

      1. Open `talkingcode-frontend/src/lib/components/layout/ChatHeader.svelte`. Currently it
         shows "TalkingCode" with a `Code2` icon and a phase badge.

      2. Update the header to include personal branding. Change the structure to:

         ```svelte
         <header class="flex h-14 items-center justify-between border-b border-border bg-background px-[var(--page-padding)]">
           <div class="flex items-center gap-3">
             <Code2 class="h-5 w-5 text-primary" />
             <div class="flex items-baseline gap-2">
               <h1 class="font-display text-lg font-semibold tracking-tight text-foreground">TalkingCode</h1>
               <span class="text-xs text-muted-foreground">Chat with Chidi's code</span>
             </div>
           </div>

           <div class="flex items-center gap-3">
             <!-- Navigation links — will add /repos in Step C.3 -->
             <nav class="flex items-center gap-1">
               <a
                 href="/"
                 class="rounded-[var(--radius-full)] px-3 py-1.5 text-sm font-medium text-foreground bg-[hsl(var(--color-primary)/0.12)]"
               >
                 Chat
               </a>
             </nav>

             {#if phase && phase !== 'idle'}
               <Badge variant="secondary" class="text-xs">{phase}</Badge>
             {/if}
           </div>
         </header>
         ```

      3. Make sure the header imports `Badge` from `$lib/components/ui/badge` and `Code2` from
         `lucide-svelte`. The `phase` prop should be typed as `string` (the `TurnPhase` type
         from the store).

      **Verify:** Run `cd talkingcode-frontend && pnpm check`. The header shows "TalkingCode"
      in Fraunces font with "Chat with Chidi's code" subtitle. A "Chat" nav pill is visible.

      Note: Header updated per structure/spec. `pnpm check` still fails on the same pre-existing
      badge prop typing issues in `InlineReasoning.svelte` and `TurnDetailPanel.svelte`.

---

- [x] **Step A.3: Replace ChatComposer with ai-elements PromptInput + ModelSelect**

      **Files to modify:**
      - `talkingcode-frontend/src/lib/components/domain/ChatComposer.svelte`

      **What to do:**

      The current ChatComposer at `talkingcode-frontend/src/lib/components/domain/ChatComposer.svelte`
      uses a raw `<textarea>` and a `<Button>`. Replace it entirely with the ai-elements
      PromptInput components that are already installed at
      `talkingcode-frontend/src/lib/components/ai-elements/prompt-input/`.

      1. Rewrite `ChatComposer.svelte` with these imports:

         ```typescript
         import {
           PromptInput,
           PromptInputBody,
           PromptInputTextarea,
           PromptInputToolbar,
           PromptInputSubmit,
           PromptInputModelSelect,
           PromptInputModelSelectTrigger,
           PromptInputModelSelectContent,
           PromptInputModelSelectItem,
           PromptInputModelSelectValue,
           type PromptInputMessage,
         } from '$lib/components/ai-elements/prompt-input';
         ```

      2. The Props interface becomes:

         ```typescript
         interface Props {
           onSubmit: (question: string) => void;
           disabled?: boolean;
           selectedModel?: string | null;
           onModelChange?: (model: string) => void;
         }

         let { onSubmit, disabled = false, selectedModel = null, onModelChange }: Props = $props();
         ```

      3. The submit handler wraps the ai-elements callback:

         ```typescript
         function handleSubmit(message: PromptInputMessage) {
           const text = message.text.trim();
           if (text && !disabled) {
             onSubmit(text);
           }
         }
         ```

      4. Define the available models:

         ```typescript
         const models = [
           { value: 'anthropic/claude-3.5-sonnet', label: 'Claude 3.5 Sonnet' },
           { value: 'google/gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
           { value: 'openai/gpt-4o', label: 'GPT-4o' },
         ];
         ```

      5. The template becomes:

         ```svelte
         <div class="border-t border-border bg-background px-[var(--page-padding)] py-4">
           <PromptInput
             onSubmit={handleSubmit}
             class="border-border/60 bg-[hsl(var(--color-surface-2))] focus-within:border-[hsl(var(--color-primary)/0.4)] focus-within:ring-2 focus-within:ring-[hsl(var(--color-primary)/0.15)]"
           >
             <PromptInputBody>
               <PromptInputTextarea
                 placeholder="Ask about architecture, modules, ownership, or behavior..."
                 disabled={disabled}
               />
             </PromptInputBody>
             <PromptInputToolbar>
               <PromptInputModelSelect
                 value={selectedModel || models[0].value}
                 onValueChange={(v) => onModelChange?.(v ?? models[0].value)}
               >
                 <PromptInputModelSelectTrigger>
                   <PromptInputModelSelectValue placeholder="Select model" />
                 </PromptInputModelSelectTrigger>
                 <PromptInputModelSelectContent>
                   {#each models as model}
                     <PromptInputModelSelectItem value={model.value}>
                       {model.label}
                     </PromptInputModelSelectItem>
                   {/each}
                 </PromptInputModelSelectContent>
               </PromptInputModelSelect>

               <PromptInputSubmit disabled={disabled} />
             </PromptInputToolbar>
           </PromptInput>
         </div>
         ```

      6. **IMPORTANT**: The `PromptInput` component is a `<form>` that internally handles
         `onsubmit`. Its `onSubmit` prop receives `(message: PromptInputMessage, event: SubmitEvent)`.
         The `PromptInputMessage` type is `{ text: string, files: FileUIPart[] }`. The textarea's
         value is automatically extracted via `FormData` with `name="message"`. You don't need
         to manage a `question` state variable — the textarea handles it internally via
         `bind:value` and `form.reset()` on submit.

      **Verify:** Run `cd talkingcode-frontend && pnpm check`. Open the app. The composer
      renders with the ai-elements PromptInput. There is a model dropdown in the toolbar showing
      "Claude 3.5 Sonnet" by default. There is a send button icon. Type text and press Enter —
      it submits. Press Shift+Enter — it adds a newline. No raw `<textarea>` or `<button>`
      elements exist in the component source.

      Note: ChatComposer now uses ai-elements PromptInput stack with ModelSelect and submit.
      `pnpm check` remains blocked by pre-existing badge typing errors outside this component.

---

- [x] **Step A.4: Wire model selector state through page and store**

      **Files to modify:**
      - `talkingcode-frontend/src/lib/stores/chatStore.svelte.ts`
      - `talkingcode-frontend/src/routes/+page.svelte`

      **What to do:**

      1. Open `talkingcode-frontend/src/lib/stores/chatStore.svelte.ts`. Add a `selectedModel`
         state variable to the store. Inside `createChatStore()`:

         ```typescript
         let selectedModel = $state<string | null>(null);
         ```

         Add to the returned object:

         ```typescript
         get selectedModel() {
           return selectedModel;
         },
         setSelectedModel(model: string) {
           selectedModel = model;
         },
         ```

      2. Open `talkingcode-frontend/src/routes/+page.svelte`. Update the `handleSubmit` function
         to pass the selected model:

         ```typescript
         async function handleSubmit(question: string) {
           chatStore.addUserMessage(question);
           const turnId = chatStore.startAssistantTurn();

           try {
             const stream = controller.startAgenticTurn({
               conversationId: null,
               question,
               model: chatStore.selectedModel  // was null before
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
         ```

      3. Update the `ChatComposer` usage in the template:

         ```svelte
         <ChatComposer
           onSubmit={handleSubmit}
           disabled={chatStore.isStreaming}
           selectedModel={chatStore.selectedModel}
           onModelChange={(model) => chatStore.setSelectedModel(model)}
         />
         ```

      **Verify:** Run `cd talkingcode-frontend && pnpm check`. Open the app. Change the model
      in the dropdown. Submit a question. Check the browser network tab — the POST to
      `/api/chat/agentic` should include `"selected_model": "google/gemini-2.5-flash"` (or
      whichever model was selected) in the request body.

      Note: Added `selectedModel` store state, setter/getter, page wiring, and composer
      `selectedModel`/`onModelChange` bindings. `pnpm check` is still blocked by pre-existing
      badge typing errors in other components.

---

### Phase B: Backend Ingestion Pipeline

- [x] **Step B.1: Set up Alembic migration infrastructure**

      **Files to create:**
      - `backend/alembic.ini`
      - `backend/alembic/env.py`
      - `backend/alembic/script.py.mako`
      - `backend/alembic/versions/` (empty directory with `__init__.py`)

      **What to do:**

      1. Run `cd /home/chidi/chatGITpt/backend && alembic init alembic` to scaffold.

      2. Edit `backend/alembic.ini`:
         - Set `script_location = alembic`
         - Comment out or leave `sqlalchemy.url` empty (will be overridden in env.py)

      3. Replace `backend/alembic/env.py` with an async-compatible version. The key parts:

         ```python
         import asyncio
         from logging.config import fileConfig

         from alembic import context
         from sqlalchemy import pool
         from sqlalchemy.ext.asyncio import create_async_engine

         from talkingcode.config import AppConfig
         from talkingcode.models.orm import Base

         config = context.config
         if config.config_file_name is not None:
             fileConfig(config.config_file_name)

         target_metadata = Base.metadata


         def get_url() -> str:
             """Get database URL from AppConfig."""
             app_config = AppConfig.from_env()
             return app_config.database_url


         def run_migrations_offline() -> None:
             """Run migrations in 'offline' mode."""
             url = get_url()
             context.configure(
                 url=url,
                 target_metadata=target_metadata,
                 literal_binds=True,
                 dialect_opts={"paramstyle": "named"},
             )
             with context.begin_transaction():
                 context.run_migrations()


         def do_run_migrations(connection):
             context.configure(connection=connection, target_metadata=target_metadata)
             with context.begin_transaction():
                 context.run_migrations()


         async def run_async_migrations() -> None:
             """Run migrations in 'online' mode with async engine."""
             engine = create_async_engine(get_url(), poolclass=pool.NullPool)
             async with engine.connect() as connection:
                 await connection.run_sync(do_run_migrations)
             await engine.dispose()


         def run_migrations_online() -> None:
             """Run migrations in 'online' mode."""
             asyncio.run(run_async_migrations())


         if context.is_offline_mode():
             run_migrations_offline()
         else:
             run_migrations_online()
         ```

      4. Generate the initial migration:
         ```bash
         cd /home/chidi/chatGITpt/backend && alembic revision --autogenerate -m "initial schema"
         ```

         This should detect all 7 tables from the ORM: `repositories`, `documents`,
         `document_chunks`, `chunk_embeddings`, `ingestion_runs`, `conversation_turns`,
         `tool_call_timeline`.

      **Verify:** The generated migration file in `backend/alembic/versions/` contains
      `create_table` operations for all 7 tables. `ruff check backend/alembic/` passes clean.
      If Alembic can't connect to the database (no Postgres running), that's OK — the migration
      file itself is the deliverable. Check it was generated and contains the right tables.

      Note: Added async Alembic env, initialized versions package, and generated
      `d4c0865a4138_initial_schema.py` with all 7 tables. Local `DATABASE_URL` auth failed, so
      migration autogeneration was run against a temporary Postgres container and validated via
      `uv run ruff check alembic/`.

---

- [ ] **Step B.2: Create domain models for ingestion**

      **Files to modify:**
      - `backend/src/talkingcode/domain/models.py`

      **What to do:**

      Open `backend/src/talkingcode/domain/models.py`. At the bottom of the file, after the
      existing `ExecuteToolGroupInput` class, add a new section with these domain dataclasses.
      Follow the exact same pattern as the existing models — all use
      `@dataclass(slots=True, frozen=True)` and import from `dataclasses` and `datetime`.

      Add these imports at the top if not already present:
      ```python
      from talkingcode.enums import IngestionStatus
      ```

      Add these classes:

      ```python
      # =============================================================================
      # Ingestion Models
      # =============================================================================

      @dataclass(slots=True, frozen=True)
      class RepositoryInfo:
          """Domain model for a tracked repository."""
          id: UUID
          provider: str
          owner: str
          name: str
          default_branch: str
          last_ingested_at: datetime | None
          created_at: datetime


      @dataclass(slots=True, frozen=True)
      class RegisterRepoInput:
          """Input for registering a new repository."""
          owner: str
          name: str
          default_branch: str = "main"
          provider: str = "github"


      @dataclass(slots=True, frozen=True)
      class IngestionRunInfo:
          """Domain model for an ingestion run."""
          id: UUID
          repository_id: UUID
          status: IngestionStatus
          started_at: datetime
          completed_at: datetime | None
          error_message: str | None


      @dataclass(slots=True, frozen=True)
      class StartIngestionInput:
          """Input for starting an ingestion run."""
          repository_id: UUID
          git_ref: str | None = None


      @dataclass(slots=True, frozen=True)
      class GitHubFileContent:
          """A single file fetched from GitHub."""
          path: str
          content: str
          sha: str


      @dataclass(slots=True, frozen=True)
      class ChunkResult:
          """A single chunk produced by the chunker."""
          content: str
          chunk_index: int
          token_count: int
          start_line: int
          end_line: int
      ```

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/`. Clean. Run
      `python -c "from talkingcode.domain.models import RepositoryInfo, RegisterRepoInput, IngestionRunInfo, StartIngestionInput, GitHubFileContent, ChunkResult; print('OK')"`.
      Prints "OK".

---

- [ ] **Step B.3: Create RepoRepository for repository + ingestion run management**

      **Files to create:**
      - `backend/src/talkingcode/repository/repo_repository.py`

      **What to do:**

      Create a new file `backend/src/talkingcode/repository/repo_repository.py`. Follow the
      exact same pattern as `conversation_repository.py`:
      - `@dataclass(slots=True)` class with `session: AsyncSession`
      - All methods are `async`
      - Returns domain models (`RepositoryInfo`, `IngestionRunInfo`), never ORM types
      - Private `_to_repo_domain()` and `_to_run_domain()` methods for ORM → domain conversion

      Here is the full file structure:

      ```python
      """Repository management repository."""
      from dataclasses import dataclass
      from datetime import datetime
      from uuid import UUID, uuid4

      from sqlalchemy import select
      from sqlalchemy.dialects.postgresql import insert
      from sqlalchemy.ext.asyncio import AsyncSession

      from talkingcode.domain.models import IngestionRunInfo, RegisterRepoInput, RepositoryInfo
      from talkingcode.enums import IngestionStatus
      from talkingcode.models.orm import IngestionRun, Repository

      import structlog

      logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


      @dataclass(slots=True)
      class RepoRepository:
          """Repository for repo management operations."""

          session: AsyncSession

          async def register(self, input_data: RegisterRepoInput) -> RepositoryInfo:
              """Register a new repo. Upsert on (provider, owner, name)."""
              stmt = insert(Repository).values(
                  id=uuid4(),
                  provider=input_data.provider,
                  owner=input_data.owner,
                  name=input_data.name,
                  default_branch=input_data.default_branch,
                  created_at=datetime.utcnow(),
              ).on_conflict_do_update(
                  constraint="uq_repo_provider_owner_name",
                  set_={
                      "default_branch": input_data.default_branch,
                  },
              )

              await self.session.execute(stmt)
              await self.session.flush()

              return await self._get_by_owner_name(input_data.owner, input_data.name)

          async def list_all(self) -> list[RepositoryInfo]:
              """List all tracked repos ordered by created_at desc."""
              result = await self.session.execute(
                  select(Repository).order_by(Repository.created_at.desc())
              )
              return [self._to_repo_domain(r) for r in result.scalars().all()]

          async def get_by_id(self, repo_id: UUID) -> RepositoryInfo | None:
              """Get a repo by ID."""
              result = await self.session.execute(
                  select(Repository).where(Repository.id == repo_id)
              )
              repo = result.scalar_one_or_none()
              return self._to_repo_domain(repo) if repo else None

          async def _get_by_owner_name(self, owner: str, name: str) -> RepositoryInfo:
              """Internal: get repo by owner/name (raises if not found)."""
              result = await self.session.execute(
                  select(Repository).where(
                      Repository.owner == owner,
                      Repository.name == name,
                  )
              )
              repo = result.scalar_one()
              return self._to_repo_domain(repo)

          async def get_by_owner_name(self, owner: str, name: str) -> RepositoryInfo | None:
              """Get a repo by owner/name."""
              result = await self.session.execute(
                  select(Repository).where(
                      Repository.owner == owner,
                      Repository.name == name,
                  )
              )
              repo = result.scalar_one_or_none()
              return self._to_repo_domain(repo) if repo else None

          async def update_last_ingested(self, repo_id: UUID, timestamp: datetime) -> None:
              """Mark a repo as recently ingested."""
              result = await self.session.execute(
                  select(Repository).where(Repository.id == repo_id)
              )
              repo = result.scalar_one_or_none()
              if repo:
                  repo.last_ingested_at = timestamp
                  await self.session.flush()

          async def create_ingestion_run(self, repo_id: UUID) -> IngestionRunInfo:
              """Create a new ingestion run in RUNNING state."""
              run = IngestionRun(
                  id=uuid4(),
                  repository_id=repo_id,
                  status=IngestionStatus.RUNNING.value,
                  started_at=datetime.utcnow(),
              )
              self.session.add(run)
              await self.session.flush()
              return self._to_run_domain(run)

          async def complete_ingestion_run(
              self,
              run_id: UUID,
              status: IngestionStatus,
              error_message: str | None = None,
          ) -> None:
              """Complete an ingestion run (done or failed)."""
              result = await self.session.execute(
                  select(IngestionRun).where(IngestionRun.id == run_id)
              )
              run = result.scalar_one_or_none()
              if run:
                  run.status = status.value
                  run.completed_at = datetime.utcnow()
                  run.error_message = error_message
                  await self.session.flush()

          async def list_ingestion_runs(self, repo_id: UUID) -> list[IngestionRunInfo]:
              """List ingestion runs for a repo, newest first."""
              result = await self.session.execute(
                  select(IngestionRun)
                  .where(IngestionRun.repository_id == repo_id)
                  .order_by(IngestionRun.started_at.desc())
              )
              return [self._to_run_domain(r) for r in result.scalars().all()]

          async def get_ingestion_run(self, run_id: UUID) -> IngestionRunInfo | None:
              """Get a single ingestion run."""
              result = await self.session.execute(
                  select(IngestionRun).where(IngestionRun.id == run_id)
              )
              run = result.scalar_one_or_none()
              return self._to_run_domain(run) if run else None

          def _to_repo_domain(self, repo: Repository) -> RepositoryInfo:
              """Convert ORM Repository to domain RepositoryInfo."""
              return RepositoryInfo(
                  id=repo.id,
                  provider=repo.provider,
                  owner=repo.owner,
                  name=repo.name,
                  default_branch=repo.default_branch,
                  last_ingested_at=repo.last_ingested_at,
                  created_at=repo.created_at,
              )

          def _to_run_domain(self, run: IngestionRun) -> IngestionRunInfo:
              """Convert ORM IngestionRun to domain IngestionRunInfo."""
              return IngestionRunInfo(
                  id=run.id,
                  repository_id=run.repository_id,
                  status=IngestionStatus(run.status),
                  started_at=run.started_at,
                  completed_at=run.completed_at,
                  error_message=run.error_message,
              )
      ```

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/talkingcode/repository/repo_repository.py`.
      Clean. Run `python -c "from talkingcode.repository.repo_repository import RepoRepository; print('OK')"`.
      Prints "OK".

---

- [ ] **Step B.4: Create GitHub file fetcher service**

      **Files to create:**
      - `backend/src/talkingcode/services/ingestion/__init__.py` (empty)
      - `backend/src/talkingcode/services/ingestion/github_fetcher.py`

      **What to do:**

      First create the `ingestion` package: `backend/src/talkingcode/services/ingestion/__init__.py`
      (empty file).

      Then create `github_fetcher.py`. Follow the service pattern from `planner_service.py`:
      Protocol interface + `@dataclass(slots=True)` implementation + structlog logger.

      ```python
      """GitHub file fetcher service."""
      import base64
      from dataclasses import dataclass
      from typing import Protocol

      import httpx
      import structlog

      from talkingcode.domain.models import GitHubFileContent
      from talkingcode.errors import InfraError

      logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

      # File extensions to index
      INDEXABLE_EXTENSIONS = {
          ".py", ".ts", ".js", ".svelte", ".rs", ".go", ".java", ".rb", ".kt",
          ".md", ".yaml", ".yml", ".toml", ".json", ".sql", ".sh", ".css",
          ".html", ".dockerfile", ".tf", ".hcl",
      }

      # File names to index (no extension)
      INDEXABLE_NAMES = {"Dockerfile", "Makefile", "Taskfile", "Justfile"}

      # Directories to skip
      SKIP_DIRS = {
          ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
          ".next", ".svelte-kit", ".mypy_cache", ".ruff_cache", ".pytest_cache",
          "target", "vendor", ".tox", "egg-info",
      }

      MAX_FILE_SIZE_BYTES = 100_000  # 100KB


      class IGitHubFetcher(Protocol):
          """Protocol for GitHub file fetching."""

          async def fetch_file_tree(self, owner: str, name: str, ref: str) -> list[str]:
              """Fetch list of indexable file paths in the repo."""
              ...

          async def fetch_file_content(self, owner: str, name: str, ref: str, path: str) -> GitHubFileContent:
              """Fetch content of a single file."""
              ...


      @dataclass(slots=True)
      class GitHubFetcher:
          """Fetches files from GitHub REST API."""

          github_token: str

          async def fetch_file_tree(self, owner: str, name: str, ref: str) -> list[str]:
              """Fetch list of indexable file paths using the Git Trees API."""
              url = f"https://api.github.com/repos/{owner}/{name}/git/trees/{ref}?recursive=1"

              async with httpx.AsyncClient() as client:
                  response = await client.get(
                      url,
                      headers={
                          "Authorization": f"token {self.github_token}",
                          "Accept": "application/vnd.github.v3+json",
                      },
                      timeout=30.0,
                  )

                  if response.status_code in (403, 429):
                      raise InfraError(f"GitHub rate limit hit: {response.status_code}")
                  response.raise_for_status()

                  data = response.json()

              paths: list[str] = []
              for item in data.get("tree", []):
                  if item.get("type") != "blob":
                      continue
                  if item.get("size", 0) > MAX_FILE_SIZE_BYTES:
                      continue

                  path = item["path"]

                  # Skip excluded directories
                  parts = path.split("/")
                  if any(part in SKIP_DIRS for part in parts):
                      continue

                  # Check extension or filename
                  filename = parts[-1]
                  if filename in INDEXABLE_NAMES:
                      paths.append(path)
                      continue

                  ext = ""
                  if "." in filename:
                      ext = "." + filename.rsplit(".", 1)[-1]
                  if ext.lower() in INDEXABLE_EXTENSIONS:
                      paths.append(path)

              logger.info("Fetched file tree", owner=owner, name=name, ref=ref, file_count=len(paths))
              return paths

          async def fetch_file_content(self, owner: str, name: str, ref: str, path: str) -> GitHubFileContent:
              """Fetch a single file's content via the Contents API."""
              url = f"https://api.github.com/repos/{owner}/{name}/contents/{path}?ref={ref}"

              async with httpx.AsyncClient() as client:
                  response = await client.get(
                      url,
                      headers={
                          "Authorization": f"token {self.github_token}",
                          "Accept": "application/vnd.github.v3+json",
                      },
                      timeout=30.0,
                  )

                  if response.status_code in (403, 429):
                      raise InfraError(f"GitHub rate limit hit for {path}: {response.status_code}")
                  response.raise_for_status()

                  data = response.json()

              content_b64 = data.get("content", "")
              content = base64.b64decode(content_b64).decode("utf-8", errors="replace")
              sha = data.get("sha", "")

              return GitHubFileContent(path=path, content=content, sha=sha)
      ```

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/talkingcode/services/ingestion/`.
      Clean. Run `python -c "from talkingcode.services.ingestion.github_fetcher import GitHubFetcher, IGitHubFetcher; print('OK')"`.
      Prints "OK".

---

- [ ] **Step B.5: Create document chunker service**

      **Files to create:**
      - `backend/src/talkingcode/services/ingestion/chunker.py`

      **What to do:**

      Create `backend/src/talkingcode/services/ingestion/chunker.py`. Follow the service pattern:
      Protocol + dataclass implementation.

      ```python
      """Document chunker service."""
      from dataclasses import dataclass
      from typing import Protocol

      import structlog

      from talkingcode.domain.models import ChunkResult

      logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


      class IChunker(Protocol):
          """Protocol for document chunking."""

          def chunk(self, content: str, max_tokens: int = 512) -> list[ChunkResult]:
              """Split content into chunks."""
              ...


      @dataclass(slots=True)
      class LineChunker:
          """Chunks documents by line groups, respecting a token budget.

          Uses whitespace-split word count as a token approximation.
          Overlap: last 2 lines of previous chunk repeat at start of next.
          """

          overlap_lines: int = 2

          def chunk(self, content: str, max_tokens: int = 512) -> list[ChunkResult]:
              """Split content into chunks."""
              if not content.strip():
                  return []

              lines = content.splitlines(keepends=True)
              chunks: list[ChunkResult] = []
              chunk_index = 0
              i = 0

              while i < len(lines):
                  current_lines: list[str] = []
                  current_tokens = 0
                  start_line = i + 1  # 1-indexed

                  while i < len(lines):
                      line_tokens = len(lines[i].split())
                      if current_tokens + line_tokens > max_tokens and current_lines:
                          break
                      current_lines.append(lines[i])
                      current_tokens += line_tokens
                      i += 1

                  if not current_lines:
                      break

                  end_line = start_line + len(current_lines) - 1
                  chunk_content = "".join(current_lines)

                  chunks.append(ChunkResult(
                      content=chunk_content,
                      chunk_index=chunk_index,
                      token_count=current_tokens,
                      start_line=start_line,
                      end_line=end_line,
                  ))

                  chunk_index += 1

                  # Apply overlap: back up by overlap_lines
                  if i < len(lines) and self.overlap_lines > 0:
                      i = max(i - self.overlap_lines, start_line + len(current_lines) - self.overlap_lines)

              logger.debug("Chunked document", chunk_count=len(chunks), total_lines=len(lines))
              return chunks
      ```

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/talkingcode/services/ingestion/chunker.py`.
      Clean. Run `python -c "
      from talkingcode.services.ingestion.chunker import LineChunker
      c = LineChunker()
      result = c.chunk('line1\nline2\nline3\nline4\nline5\n' * 20, max_tokens=10)
      print(f'{len(result)} chunks')
      assert len(result) > 1, 'Should produce multiple chunks'
      print('OK')
      "`. Prints chunk count and "OK".

---

- [ ] **Step B.6: Create embedding generator service**

      **Files to create:**
      - `backend/src/talkingcode/services/ingestion/embedder.py`

      **What to do:**

      Create `backend/src/talkingcode/services/ingestion/embedder.py`. Protocol + dataclass.
      Uses `httpx.AsyncClient` to call OpenAI Embeddings API.

      ```python
      """Embedding generator service."""
      import asyncio
      from dataclasses import dataclass
      from typing import Protocol

      import httpx
      import structlog

      from talkingcode.errors import InfraError

      logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

      OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
      MAX_BATCH_SIZE = 100
      MAX_RETRIES = 3


      class IEmbedder(Protocol):
          """Protocol for embedding generation."""

          async def embed_batch(self, texts: list[str]) -> list[list[float]]:
              """Generate embeddings for a batch of texts."""
              ...


      @dataclass(slots=True)
      class OpenAIEmbedder:
          """Generates embeddings using OpenAI's API."""

          openai_api_key: str
          model: str = "text-embedding-3-small"
          dimensions: int = 1536

          async def embed_batch(self, texts: list[str]) -> list[list[float]]:
              """Generate embeddings for a batch of texts.

              Splits into sub-batches of MAX_BATCH_SIZE and retries on failure.
              """
              if not texts:
                  return []

              all_embeddings: list[list[float]] = []

              for batch_start in range(0, len(texts), MAX_BATCH_SIZE):
                  batch = texts[batch_start:batch_start + MAX_BATCH_SIZE]
                  embeddings = await self._embed_single_batch(batch)
                  all_embeddings.extend(embeddings)

              logger.info("Generated embeddings", count=len(all_embeddings), model=self.model)
              return all_embeddings

          async def _embed_single_batch(self, texts: list[str]) -> list[list[float]]:
              """Embed a single batch with retry."""
              for attempt in range(MAX_RETRIES):
                  try:
                      async with httpx.AsyncClient() as client:
                          response = await client.post(
                              OPENAI_EMBEDDINGS_URL,
                              headers={
                                  "Authorization": f"Bearer {self.openai_api_key}",
                                  "Content-Type": "application/json",
                              },
                              json={
                                  "model": self.model,
                                  "input": texts,
                                  "dimensions": self.dimensions,
                              },
                              timeout=60.0,
                          )

                          if response.status_code in (429, 503):
                              wait = 2 ** attempt
                              logger.warning("Rate limited, retrying", attempt=attempt, wait_seconds=wait)
                              await asyncio.sleep(wait)
                              continue

                          response.raise_for_status()
                          data = response.json()

                          # Sort by index to preserve order
                          sorted_data = sorted(data["data"], key=lambda x: x["index"])
                          return [item["embedding"] for item in sorted_data]

                  except httpx.HTTPStatusError as e:
                      if attempt == MAX_RETRIES - 1:
                          raise InfraError(f"OpenAI embedding failed after {MAX_RETRIES} retries: {e}") from e
                      wait = 2 ** attempt
                      logger.warning("Embedding request failed, retrying", attempt=attempt, error=str(e))
                      await asyncio.sleep(wait)

              raise InfraError("OpenAI embedding failed: max retries exceeded")
      ```

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/talkingcode/services/ingestion/embedder.py`.
      Clean. Run `python -c "from talkingcode.services.ingestion.embedder import OpenAIEmbedder, IEmbedder; print('OK')"`.
      Prints "OK".

---

- [ ] **Step B.7: Create ingestion orchestrator service**

      **Files to create:**
      - `backend/src/talkingcode/services/ingestion/ingestion_service.py`

      **What to do:**

      This is the main orchestrator. It ties together: GitHub fetcher, classifier, chunker,
      embedder, document repository, and repo repository.

      Create `backend/src/talkingcode/services/ingestion/ingestion_service.py`:

      ```python
      """Ingestion orchestrator service."""
      import hashlib
      from dataclasses import dataclass
      from datetime import datetime
      from typing import Protocol

      import structlog

      from talkingcode.domain.models import IngestionRunInfo, StartIngestionInput
      from talkingcode.enums import IngestionStatus
      from talkingcode.repository.document_repository import DocumentRepository
      from talkingcode.repository.repo_repository import RepoRepository
      from talkingcode.services.classification.document_classifier import IDocumentClassifier
      from talkingcode.services.ingestion.chunker import IChunker
      from talkingcode.services.ingestion.embedder import IEmbedder
      from talkingcode.services.ingestion.github_fetcher import IGitHubFetcher

      logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


      class IIngestionService(Protocol):
          """Protocol for ingestion orchestration."""

          async def run_ingestion(self, input_data: StartIngestionInput) -> IngestionRunInfo:
              """Run a full ingestion pipeline for a repository."""
              ...


      @dataclass(slots=True)
      class IngestionService:
          """Orchestrates the full ingestion pipeline."""

          repo_repository: RepoRepository
          document_repository: DocumentRepository
          github_fetcher: IGitHubFetcher
          classifier: IDocumentClassifier
          chunker: IChunker
          embedder: IEmbedder

          async def run_ingestion(self, input_data: StartIngestionInput) -> IngestionRunInfo:
              """Run a full ingestion pipeline.

              Steps:
              1. Look up the repository
              2. Create ingestion run (RUNNING)
              3. Fetch file tree from GitHub
              4. For each file: fetch, classify, chunk, embed, persist
              5. Mark repo as recently ingested
              6. Complete ingestion run (DONE or FAILED)
              """
              repo = await self.repo_repository.get_by_id(input_data.repository_id)
              if not repo:
                  raise ValueError(f"Repository {input_data.repository_id} not found")

              git_ref = input_data.git_ref or repo.default_branch
              run = await self.repo_repository.create_ingestion_run(repo.id)

              logger.info(
                  "Starting ingestion",
                  repo=f"{repo.owner}/{repo.name}",
                  ref=git_ref,
                  run_id=str(run.id),
              )

              try:
                  # Fetch file tree
                  paths = await self.github_fetcher.fetch_file_tree(
                      owner=repo.owner, name=repo.name, ref=git_ref
                  )
                  logger.info("File tree fetched", file_count=len(paths))

                  for idx, path in enumerate(paths):
                      logger.info(
                          "Ingesting file",
                          progress=f"{idx + 1}/{len(paths)}",
                          path=path,
                      )

                      try:
                          # Fetch file content
                          file_content = await self.github_fetcher.fetch_file_content(
                              owner=repo.owner, name=repo.name, ref=git_ref, path=path
                          )

                          # Compute SHA256
                          content_sha = hashlib.sha256(
                              file_content.content.encode("utf-8")
                          ).hexdigest()

                          # Classify the document
                          from talkingcode.domain.models import DocumentClassificationInput
                          classification = await self.classifier.classify(
                              DocumentClassificationInput(
                                  repo=f"{repo.owner}/{repo.name}",
                                  path=path,
                                  content=file_content.content[:2000],  # first 2K chars for classification
                              )
                          )

                          classification_dict = {
                              "language": classification.language,
                              "area": classification.area.value,
                              "file_type": classification.file_type.value,
                              "symbols": classification.symbols,
                              "tags": classification.tags,
                          }

                          # Save/upsert document
                          doc_id = await self.document_repository.save_document(
                              repository_id=repo.id,
                              path=path,
                              content_sha=content_sha,
                              git_ref=git_ref,
                              classification=classification_dict,
                          )

                          # Chunk the content
                          chunks = self.chunker.chunk(file_content.content)

                          if not chunks:
                              continue

                          # Save chunks and collect texts for embedding
                          chunk_ids: list = []
                          chunk_texts: list[str] = []

                          for chunk in chunks:
                              chunk_id = await self.document_repository.save_chunk(
                                  document_id=doc_id,
                                  chunk_index=chunk.chunk_index,
                                  content=chunk.content,
                                  token_count=chunk.token_count,
                                  metadata=classification_dict,
                              )
                              chunk_ids.append(chunk_id)
                              chunk_texts.append(chunk.content)

                          # Generate embeddings in batch
                          embeddings = await self.embedder.embed_batch(chunk_texts)

                          # Save embeddings
                          for chunk_id, embedding in zip(chunk_ids, embeddings, strict=True):
                              await self.document_repository.save_chunk_embedding(
                                  chunk_id=chunk_id,
                                  embedding=embedding,
                                  model=self.embedder.model,
                              )

                      except Exception as file_err:
                          logger.warning(
                              "Failed to ingest file, skipping",
                              path=path,
                              error=str(file_err),
                          )
                          continue

                  # Mark repo as recently ingested
                  await self.repo_repository.update_last_ingested(repo.id, datetime.utcnow())

                  # Complete run as DONE
                  await self.repo_repository.complete_ingestion_run(
                      run_id=run.id, status=IngestionStatus.DONE
                  )

                  logger.info("Ingestion completed", repo=f"{repo.owner}/{repo.name}", run_id=str(run.id))

              except Exception as e:
                  logger.error("Ingestion failed", repo=f"{repo.owner}/{repo.name}", error=str(e))
                  await self.repo_repository.complete_ingestion_run(
                      run_id=run.id,
                      status=IngestionStatus.FAILED,
                      error_message=str(e),
                  )

              # Return the final state of the run
              final_run = await self.repo_repository.get_ingestion_run(run.id)
              return final_run or run
      ```

      **IMPORTANT NOTE about `self.embedder.model`**: The `OpenAIEmbedder` has a `model` field.
      When accessing it in the orchestrator via `self.embedder.model`, this works because
      `IEmbedder` Protocol doesn't declare `model` but the concrete `OpenAIEmbedder` dataclass
      has it. If the type checker complains, you can either: (a) add `model: str` to the
      `IEmbedder` Protocol, or (b) pass the embedding model name as a constructor parameter
      to `IngestionService` instead. Choose whichever makes `ruff check` pass.

      Also: The `IDocumentClassifier` Protocol needs to exist. Check
      `backend/src/talkingcode/services/classification/document_classifier.py` — if it doesn't
      have a Protocol, add one. It should have `async def classify(self, input_data: DocumentClassificationInput) -> DocumentClassificationOutput`.

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/talkingcode/services/ingestion/`.
      Clean. Run `python -c "from talkingcode.services.ingestion.ingestion_service import IngestionService, IIngestionService; print('OK')"`.
      Prints "OK".

---

- [ ] **Step B.8: Create ingestion controller**

      **Files to create:**
      - `backend/src/talkingcode/controllers/ingestion_controller.py`

      **What to do:**

      Create `backend/src/talkingcode/controllers/ingestion_controller.py`. Follow the exact
      pattern of `chat_controller.py`: `@dataclass(slots=True)`, structlog logger, no business
      logic — just delegation.

      ```python
      """Ingestion controller."""
      from dataclasses import dataclass

      import structlog

      from talkingcode.domain.models import (
          IngestionRunInfo,
          RegisterRepoInput,
          RepositoryInfo,
          StartIngestionInput,
      )
      from talkingcode.errors import NotFoundError
      from talkingcode.repository.repo_repository import RepoRepository
      from talkingcode.services.ingestion.ingestion_service import IIngestionService

      logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)


      @dataclass(slots=True)
      class IngestionController:
          """Controller for repo management and ingestion operations."""

          repo_repository: RepoRepository
          ingestion_service: IIngestionService

          async def register_repo(self, input_data: RegisterRepoInput) -> RepositoryInfo:
              """Register a new repository for tracking."""
              logger.info("Registering repo", owner=input_data.owner, name=input_data.name)
              return await self.repo_repository.register(input_data)

          async def list_repos(self) -> list[RepositoryInfo]:
              """List all tracked repositories."""
              return await self.repo_repository.list_all()

          async def get_repo(self, owner: str, name: str) -> RepositoryInfo:
              """Get a specific repository. Raises NotFoundError if not found."""
              repo = await self.repo_repository.get_by_owner_name(owner, name)
              if not repo:
                  raise NotFoundError(resource=f"Repository {owner}/{name}")
              return repo

          async def start_ingestion(
              self, owner: str, name: str, git_ref: str | None = None
          ) -> IngestionRunInfo:
              """Start an ingestion run for a repository."""
              repo = await self.repo_repository.get_by_owner_name(owner, name)
              if not repo:
                  raise NotFoundError(resource=f"Repository {owner}/{name}")

              logger.info("Starting ingestion", repo=f"{owner}/{name}", ref=git_ref)
              return await self.ingestion_service.run_ingestion(
                  StartIngestionInput(repository_id=repo.id, git_ref=git_ref)
              )

          async def list_ingestion_runs(
              self, owner: str, name: str
          ) -> list[IngestionRunInfo]:
              """List ingestion runs for a repository."""
              repo = await self.repo_repository.get_by_owner_name(owner, name)
              if not repo:
                  raise NotFoundError(resource=f"Repository {owner}/{name}")
              return await self.repo_repository.list_ingestion_runs(repo.id)
      ```

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/talkingcode/controllers/ingestion_controller.py`.
      Clean. Run `python -c "from talkingcode.controllers.ingestion_controller import IngestionController; print('OK')"`.
      Prints "OK".

---

- [ ] **Step B.9: Create repo management and ingestion routes**

      **Files to create:**
      - `backend/src/talkingcode/routes/repo_routes.py`

      **Files to modify:**
      - `backend/src/talkingcode/app.py` (register new router)

      **What to do:**

      1. Create `backend/src/talkingcode/routes/repo_routes.py`. Follow the exact pattern of
         `chat_routes.py`: `APIRouter()`, Pydantic request models, factory dependency injection.

         ```python
         """Repository management routes."""
         from dataclasses import asdict

         from fastapi import APIRouter, Depends
         from pydantic import BaseModel

         from talkingcode.dependencies import FactoryDep
         from talkingcode.domain.models import RegisterRepoInput
         from talkingcode.factory import AppFactory

         router = APIRouter()


         class RegisterRepoRequest(BaseModel):
             """Request body for registering a repository."""
             owner: str
             name: str
             default_branch: str = "main"


         class StartIngestionRequest(BaseModel):
             """Request body for starting an ingestion run."""
             git_ref: str | None = None


         def _serialize_repo(repo):
             """Serialize a RepositoryInfo to a JSON-safe dict."""
             d = asdict(repo)
             d["id"] = str(d["id"])
             if d["last_ingested_at"]:
                 d["last_ingested_at"] = d["last_ingested_at"].isoformat()
             d["created_at"] = d["created_at"].isoformat()
             return d


         def _serialize_run(run):
             """Serialize an IngestionRunInfo to a JSON-safe dict."""
             d = asdict(run)
             d["id"] = str(d["id"])
             d["repository_id"] = str(d["repository_id"])
             d["status"] = d["status"].value if hasattr(d["status"], "value") else d["status"]
             d["started_at"] = d["started_at"].isoformat()
             if d["completed_at"]:
                 d["completed_at"] = d["completed_at"].isoformat()
             return d


         @router.post("/repos")
         async def register_repo(body: RegisterRepoRequest, factory: FactoryDep) -> dict:
             """Register a GitHub repository for ingestion."""
             controller = factory.get_ingestion_controller()
             repo = await controller.register_repo(
                 RegisterRepoInput(
                     owner=body.owner,
                     name=body.name,
                     default_branch=body.default_branch,
                 )
             )
             return _serialize_repo(repo)


         @router.get("/repos")
         async def list_repos(factory: FactoryDep) -> list[dict]:
             """List all tracked repositories."""
             controller = factory.get_ingestion_controller()
             repos = await controller.list_repos()
             return [_serialize_repo(r) for r in repos]


         @router.get("/repos/{owner}/{name}")
         async def get_repo(owner: str, name: str, factory: FactoryDep) -> dict:
             """Get details of a specific repository."""
             controller = factory.get_ingestion_controller()
             repo = await controller.get_repo(owner, name)
             return _serialize_repo(repo)


         @router.post("/repos/{owner}/{name}/ingest")
         async def start_ingestion(
             owner: str,
             name: str,
             factory: FactoryDep,
             body: StartIngestionRequest | None = None,
         ) -> dict:
             """Start an ingestion run. Synchronous — completes when ingestion is done."""
             controller = factory.get_ingestion_controller()
             git_ref = body.git_ref if body else None
             run = await controller.start_ingestion(owner, name, git_ref)
             return _serialize_run(run)


         @router.get("/repos/{owner}/{name}/runs")
         async def list_ingestion_runs(
             owner: str, name: str, factory: FactoryDep
         ) -> list[dict]:
             """List ingestion run history for a repository."""
             controller = factory.get_ingestion_controller()
             runs = await controller.list_ingestion_runs(owner, name)
             return [_serialize_run(r) for r in runs]
         ```

      2. Open `backend/src/talkingcode/app.py`. Add the new router import and registration.
         After the existing line:
         ```python
         from talkingcode.routes import chat_routes
         app.include_router(chat_routes.router, prefix="/chat", tags=["chat"])
         ```

         Add:
         ```python
         from talkingcode.routes import repo_routes
         app.include_router(repo_routes.router, tags=["repos"])
         ```

         Note: no prefix for repo_routes because the routes already include `/repos` in their
         path decorators.

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/`. Clean. Run
      `python -c "from talkingcode.app import app; print('OK')"`. Prints "OK".

---

- [ ] **Step B.10: Wire ingestion into AppFactory**

      **Files to modify:**
      - `backend/src/talkingcode/factory.py`

      **What to do:**

      Open `backend/src/talkingcode/factory.py`. Add imports for all new services and the
      repo repository. Then add factory methods following the existing pattern.

      1. Add these imports at the top of the file (after existing imports):

         ```python
         from talkingcode.repository.repo_repository import RepoRepository
         from talkingcode.services.ingestion.chunker import LineChunker
         from talkingcode.services.ingestion.embedder import OpenAIEmbedder
         from talkingcode.services.ingestion.github_fetcher import GitHubFetcher
         from talkingcode.services.ingestion.ingestion_service import IngestionService
         ```

      2. Add to the `TYPE_CHECKING` block:

         ```python
         from talkingcode.controllers.ingestion_controller import IngestionController
         ```

      3. Add these methods to the `AppFactory` class (after `get_chat_controller`):

         ```python
         def get_repo_repository(self) -> RepoRepository:
             """Get repo repository."""
             return RepoRepository(self.session)

         def get_github_fetcher(self) -> GitHubFetcher:
             """Get GitHub file fetcher."""
             return GitHubFetcher(github_token=self.config.github_token)

         def get_chunker(self) -> LineChunker:
             """Get document chunker."""
             return LineChunker()

         def get_embedder(self) -> OpenAIEmbedder:
             """Get embedding generator."""
             return OpenAIEmbedder(
                 openai_api_key=self.config.openai_api_key,
                 model=self.config.embedding_model,
                 dimensions=self.config.embedding_dimensions,
             )

         def get_ingestion_service(self) -> IngestionService:
             """Get ingestion orchestrator service."""
             return IngestionService(
                 repo_repository=self.get_repo_repository(),
                 document_repository=self.get_document_repository(),
                 github_fetcher=self.get_github_fetcher(),
                 classifier=self.get_document_classifier(),
                 chunker=self.get_chunker(),
                 embedder=self.get_embedder(),
             )

         def get_ingestion_controller(self) -> "IngestionController":
             """Get ingestion controller."""
             from talkingcode.controllers.ingestion_controller import IngestionController

             return IngestionController(
                 repo_repository=self.get_repo_repository(),
                 ingestion_service=self.get_ingestion_service(),
             )
         ```

      **Verify:** Run `cd /home/chidi/chatGITpt/backend && ruff check src/talkingcode/factory.py`.
      Clean. Run `python -c "from talkingcode.factory import AppFactory; print('OK')"`.
      Prints "OK".

---

- [ ] **Step B.11: Backend integration verification**

      **What to do:**

      Run the full backend verification suite:

      1. `cd /home/chidi/chatGITpt/backend && ruff check src/` — must be clean
      2. `python -c "from talkingcode.app import app; print('OK')"` — app imports without error
      3. If a database is available (check `docker compose ps` or similar):
         - Start the backend: `uvicorn talkingcode.app:app --host 0.0.0.0 --port 8000`
         - `curl -s http://localhost:8000/health` → `{"status":"ok"}`
         - `curl -s http://localhost:8000/openapi.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(sorted(d['paths'].keys()))"` → should show paths including `/repos`, `/repos/{owner}/{name}`, `/repos/{owner}/{name}/ingest`, `/repos/{owner}/{name}/runs`, `/chat/agentic`, `/chat/timeline`, `/health`
      4. If no database is available, just verify the import checks pass.

      **Verify:** At minimum, steps 1-2 pass. If DB is available, all 7+ routes appear in OpenAPI.

---

### Phase C: Frontend Repo Management

- [ ] **Step C.1: Add frontend types and service for repo management**

      **Files to modify:**
      - `talkingcode-frontend/src/lib/models/index.ts`

      **Files to create:**
      - `talkingcode-frontend/src/lib/services/IRepoService.ts`
      - `talkingcode-frontend/src/lib/services/RepoService.ts`

      **What to do:**

      1. Open `talkingcode-frontend/src/lib/models/index.ts`. At the bottom of the file, add:

         ```typescript
         // =============================================================================
         // Repository Management
         // =============================================================================

         export interface RepositoryInfo {
           id: string;
           provider: string;
           owner: string;
           name: string;
           default_branch: string;
           last_ingested_at: string | null;
           created_at: string;
         }

         export interface IngestionRunInfo {
           id: string;
           repository_id: string;
           status: 'running' | 'done' | 'failed';
           started_at: string;
           completed_at: string | null;
           error_message: string | null;
         }

         export interface RegisterRepoInput {
           owner: string;
           name: string;
           defaultBranch?: string;
         }
         ```

      2. Create `talkingcode-frontend/src/lib/services/IRepoService.ts`:

         ```typescript
         /** Repo service interface */
         import type { RepositoryInfo, IngestionRunInfo, RegisterRepoInput } from '$lib/models';

         export interface IRepoService {
           listRepos(): Promise<RepositoryInfo[]>;
           getRepo(owner: string, name: string): Promise<RepositoryInfo>;
           registerRepo(input: RegisterRepoInput): Promise<RepositoryInfo>;
           startIngestion(owner: string, name: string, gitRef?: string): Promise<IngestionRunInfo>;
           listIngestionRuns(owner: string, name: string): Promise<IngestionRunInfo[]>;
         }
         ```

      3. Create `talkingcode-frontend/src/lib/services/RepoService.ts`. Follow the same pattern
         as `ChatService.ts` — class with `backendUrl` from env:

         ```typescript
         /** Repo service implementation */
         import type { RepositoryInfo, IngestionRunInfo, RegisterRepoInput } from '$lib/models';
         import type { IRepoService } from './IRepoService';

         export class RepoService implements IRepoService {
           async listRepos(): Promise<RepositoryInfo[]> {
             const response = await fetch('/api/repos');
             if (!response.ok) throw new Error(`Failed to list repos: ${response.status}`);
             return response.json();
           }

           async getRepo(owner: string, name: string): Promise<RepositoryInfo> {
             const response = await fetch(`/api/repos/${owner}/${name}`);
             if (!response.ok) throw new Error(`Failed to get repo: ${response.status}`);
             return response.json();
           }

           async registerRepo(input: RegisterRepoInput): Promise<RepositoryInfo> {
             const response = await fetch('/api/repos', {
               method: 'POST',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify({
                 owner: input.owner,
                 name: input.name,
                 default_branch: input.defaultBranch || 'main',
               }),
             });
             if (!response.ok) throw new Error(`Failed to register repo: ${response.status}`);
             return response.json();
           }

           async startIngestion(owner: string, name: string, gitRef?: string): Promise<IngestionRunInfo> {
             const response = await fetch(`/api/repos/${owner}/${name}/ingest`, {
               method: 'POST',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify({ git_ref: gitRef || null }),
             });
             if (!response.ok) throw new Error(`Failed to start ingestion: ${response.status}`);
             return response.json();
           }

           async listIngestionRuns(owner: string, name: string): Promise<IngestionRunInfo[]> {
             const response = await fetch(`/api/repos/${owner}/${name}/runs`);
             if (!response.ok) throw new Error(`Failed to list runs: ${response.status}`);
             return response.json();
           }
         }
         ```

         **NOTE:** The `RepoService` uses `/api/repos/...` (SvelteKit API routes, not the
         direct backend URL). This is because we need SvelteKit to proxy to the backend.
         The API proxy routes will be created in Step C.2.

      **Verify:** Run `cd talkingcode-frontend && pnpm check`. Clean. No type errors.

---

- [ ] **Step C.2: Create SvelteKit API proxy routes for repo management**

      **Files to create:**
      - `talkingcode-frontend/src/routes/api/repos/+server.ts`
      - `talkingcode-frontend/src/routes/api/repos/[owner]/[name]/+server.ts`
      - `talkingcode-frontend/src/routes/api/repos/[owner]/[name]/ingest/+server.ts`
      - `talkingcode-frontend/src/routes/api/repos/[owner]/[name]/runs/+server.ts`

      **What to do:**

      Each proxy route forwards the request to the backend. Look at the existing
      `talkingcode-frontend/src/routes/api/chat/agentic/+server.ts` for the pattern. The backend
      URL comes from `$env/dynamic/private` (or `$env/static/private`). Check which one the
      existing agentic route uses and follow the same approach.

      Here's the pattern for each route:

      **`/api/repos/+server.ts` (handles GET and POST):**
      ```typescript
      import { env } from '$env/dynamic/private';
      import type { RequestHandler } from './$types';

      const BACKEND_URL = env.BACKEND_URL || 'http://localhost:8000';

      export const GET: RequestHandler = async ({ fetch }) => {
        const response = await fetch(`${BACKEND_URL}/repos`);
        const data = await response.json();
        return new Response(JSON.stringify(data), {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        });
      };

      export const POST: RequestHandler = async ({ request, fetch }) => {
        const body = await request.json();
        const response = await fetch(`${BACKEND_URL}/repos`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        const data = await response.json();
        return new Response(JSON.stringify(data), {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        });
      };
      ```

      Follow the same pattern for the other routes, adjusting the URL path and methods.

      **IMPORTANT:** Check how the existing `api/chat/agentic/+server.ts` gets the backend URL.
      Use the same mechanism. It might use `env.PUBLIC_BACKEND_URL` or `env.BACKEND_URL` or
      something else. Be consistent.

      **Verify:** Run `cd talkingcode-frontend && pnpm check`. Clean. All route files compile.

---

- [ ] **Step C.3: Create the repos page, components, and navigation**

      **Files to create:**
      - `talkingcode-frontend/src/routes/repos/+page.svelte`
      - `talkingcode-frontend/src/routes/repos/+page.server.ts`
      - `talkingcode-frontend/src/lib/components/domain/RepoCard.svelte`
      - `talkingcode-frontend/src/lib/components/domain/RegisterRepoForm.svelte`
      - `talkingcode-frontend/src/lib/components/domain/IngestionHistory.svelte`

      **Files to modify:**
      - `talkingcode-frontend/src/lib/components/layout/ChatHeader.svelte` (add /repos nav link)
      - `talkingcode-frontend/src/lib/components/domain/index.ts` (export new components)

      **What to do:**

      **1. Navigation — Update ChatHeader.svelte:**

      Open `talkingcode-frontend/src/lib/components/layout/ChatHeader.svelte`. Update the nav
      section to include both Chat and Repos links. Add a `currentPath` prop:

      ```typescript
      interface Props {
        phase?: string;
        currentPath?: string;
      }

      let { phase, currentPath = '/' }: Props = $props();
      ```

      Render navigation links:
      ```svelte
      <nav class="flex items-center gap-1">
        <a
          href="/"
          class="rounded-[var(--radius-full)] px-3 py-1.5 text-sm font-medium transition-colors
            {currentPath === '/' ? 'text-foreground bg-[hsl(var(--color-primary)/0.12)]' : 'text-muted-foreground hover:text-foreground'}"
        >
          Chat
        </a>
        <a
          href="/repos"
          class="rounded-[var(--radius-full)] px-3 py-1.5 text-sm font-medium transition-colors
            {currentPath === '/repos' ? 'text-foreground bg-[hsl(var(--color-primary)/0.12)]' : 'text-muted-foreground hover:text-foreground'}"
        >
          Repos
        </a>
      </nav>
      ```

      Update `+page.svelte` (the chat page) to pass `currentPath="/"` to `ChatHeader`.
      You'll need to import `page` from `$app/stores` or just hardcode it since that page
      is always `/`.

      **2. Page server — `repos/+page.server.ts`:**

      ```typescript
      import type { PageServerLoad } from './$types';

      export const load: PageServerLoad = async ({ fetch }) => {
        try {
          const response = await fetch('/api/repos');
          if (!response.ok) return { repos: [] };
          const repos = await response.json();
          return { repos };
        } catch {
          return { repos: [] };
        }
      };
      ```

      **3. RepoCard.svelte:**

      Props: `repo: RepositoryInfo`, `onIngest: (owner: string, name: string) => void`,
      `ingesting: boolean`.

      Uses the `Card` primitive (if it exists in `primitives/`) or raw div with card styling.
      Shows:
      - Title: `{repo.owner}/{repo.name}` in `font-medium text-foreground`
      - GitHub icon (import from `lucide-svelte`)
      - Default branch as a `Badge` (variant="secondary")
      - "Last ingested: {relative time}" or "Never ingested" in `text-xs text-muted-foreground`
      - "Ingest now" `Button` (variant="default", size="sm")
      - Loading state on button when `ingesting` is true

      Style the card: `rounded-[var(--radius-lg)] border border-border bg-[hsl(var(--color-surface-2))] p-[var(--card-padding)]`

      **4. RegisterRepoForm.svelte:**

      A simple inline form with:
      - Owner text input
      - Name text input
      - Default branch text input (defaults to "main")
      - Submit button

      Props: `onRegister: (input: RegisterRepoInput) => void`, `loading: boolean`.

      Use shadcn `Input` and `Button` components. Style with design system tokens.

      **5. IngestionHistory.svelte:**

      Props: `runs: IngestionRunInfo[]`.

      Renders a list of runs with:
      - Status badge: `running` = amber/warning, `done` = green/success, `failed` = red/danger
      - Started at timestamp
      - Duration if completed
      - Error message if failed (truncated)

      Use `Badge` for status.

      **6. Repos page — `repos/+page.svelte`:**

      ```svelte
      <script lang="ts">
        import { ChatLayout, ChatHeader } from '$lib/components/layout';
        import { RepoCard, RegisterRepoForm, IngestionHistory } from '$lib/components/domain';
        import { RepoService } from '$lib/services/RepoService';
        import type { RepositoryInfo, IngestionRunInfo, RegisterRepoInput } from '$lib/models';

        let { data } = $props();

        const repoService = new RepoService();
        let repos = $state<RepositoryInfo[]>(data.repos || []);
        let ingestingRepos = $state<Set<string>>(new Set());
        let registering = $state(false);
        let showRegisterForm = $state(false);

        async function handleRegister(input: RegisterRepoInput) {
          registering = true;
          try {
            const repo = await repoService.registerRepo(input);
            repos = [repo, ...repos.filter(r => r.id !== repo.id)];
            showRegisterForm = false;
          } catch (err) {
            // TODO: toast error
            console.error(err);
          } finally {
            registering = false;
          }
        }

        async function handleIngest(owner: string, name: string) {
          const key = `${owner}/${name}`;
          ingestingRepos.add(key);
          ingestingRepos = new Set(ingestingRepos);
          try {
            await repoService.startIngestion(owner, name);
            // Refresh repos list
            repos = await repoService.listRepos();
          } catch (err) {
            console.error(err);
          } finally {
            ingestingRepos.delete(key);
            ingestingRepos = new Set(ingestingRepos);
          }
        }
      </script>

      <ChatLayout>
        <ChatHeader phase={undefined} currentPath="/repos" />

        <main class="flex-1 overflow-y-auto px-[var(--page-padding)] py-8">
          <div class="mx-auto max-w-3xl">
            <div class="mb-8 flex items-center justify-between">
              <h1 class="font-display text-2xl font-semibold tracking-tight text-foreground">
                Repositories
              </h1>
              <Button onclick={() => showRegisterForm = !showRegisterForm}>
                {showRegisterForm ? 'Cancel' : 'Register repo'}
              </Button>
            </div>

            {#if showRegisterForm}
              <div class="mb-8">
                <RegisterRepoForm onRegister={handleRegister} loading={registering} />
              </div>
            {/if}

            {#if repos.length === 0}
              <EmptyState
                title="No repositories tracked"
                description="Register a GitHub repository to start indexing its code for chat."
              />
            {:else}
              <div class="grid gap-4">
                {#each repos as repo (repo.id)}
                  <RepoCard
                    {repo}
                    onIngest={handleIngest}
                    ingesting={ingestingRepos.has(`${repo.owner}/${repo.name}`)}
                  />
                {/each}
              </div>
            {/if}
          </div>
        </main>
      </ChatLayout>
      ```

      Make sure to import `Button` from `$lib/components/ui/button` and `EmptyState` from
      `$lib/components/layout`. Import `Badge` from `$lib/components/ui/badge`.

      **7. Update domain index:**

      Open `talkingcode-frontend/src/lib/components/domain/index.ts` and add exports:
      ```typescript
      export { default as RepoCard } from './RepoCard.svelte';
      export { default as RegisterRepoForm } from './RegisterRepoForm.svelte';
      export { default as IngestionHistory } from './IngestionHistory.svelte';
      ```

      **Verify:** Run `cd talkingcode-frontend && pnpm check`. Navigate to `/repos` in browser.
      Page renders with "Repositories" heading. Navigation between Chat and Repos works.
      If no backend, the empty state shows "No repositories tracked".

---

- [ ] **Step C.4: Wire ingestion actions on the repos page**

      **Files to modify:**
      - `talkingcode-frontend/src/routes/repos/+page.svelte` (if needed)
      - `talkingcode-frontend/src/lib/components/domain/RepoCard.svelte`

      **What to do:**

      This step ensures all interactive actions work end-to-end:

      1. **Register repo**: The `RegisterRepoForm` submits, `handleRegister` calls
         `repoService.registerRepo()`. On success, the new repo appears in the list.
         On error, log to console (toast deferred).

      2. **Ingest now**: The `RepoCard` "Ingest now" button calls `handleIngest(owner, name)`.
         The button shows a loading state (spinner or disabled) while ingesting. On completion,
         the repo card shows updated `last_ingested_at`.

      3. **Ingestion history**: Add an expandable section to `RepoCard.svelte` that fetches
         and displays ingestion runs when clicked. Use the shadcn `Collapsible` component
         or a simple `{#if}` toggle.

         When the user clicks "Show history" on a RepoCard:
         - Fetch runs from `repoService.listIngestionRuns(repo.owner, repo.name)`
         - Display using the `IngestionHistory` component
         - Cache the runs in local state so they don't refetch every toggle

      **Verify:** With both frontend and backend running:
      - Register a repo (e.g., `chidinweke/chatGITpt`)
      - Repo card appears with "Never ingested"
      - Click "Ingest now" — button shows loading state
      - On completion, "Last ingested: just now" appears
      - Expand history — shows the completed run with "done" badge

      If backend is not running, verify that:
      - The UI renders without crashing
      - Error states are handled (no blank screen)
      - `pnpm check` passes clean

---

### Phase D: Integration & Polish

- [ ] **Step D.1: Design system audit**

      **What to do:**

      Systematically audit ALL frontend files for design system violations. This is a grep-based
      search and fix pass.

      1. **Search for raw Tailwind colours:**
         ```bash
         cd /home/chidi/chatGITpt/talkingcode-frontend
         grep -rn "bg-white\|text-gray-\|text-blue-\|bg-gray-\|border-gray-" src/ --include="*.svelte" --include="*.ts"
         ```
         Replace every match:
         - `bg-white` → `bg-background` or `bg-[hsl(var(--color-surface))]`
         - `text-gray-*` → `text-muted-foreground` or `text-foreground`
         - `bg-gray-*` → `bg-muted` or `bg-[hsl(var(--color-surface-2))]`
         - `border-gray-*` → `border-border`
         - `text-blue-*` → `text-primary`

      2. **Check typography:**
         - All heading elements (`<h1>` through `<h4>`) must use `font-display` (Fraunces)
           with `tracking-tight`
         - Body text should use the default font (DM Sans, set in app.css)
         - `grep -rn "font-family" src/ --include="*.svelte"` → should return nothing custom

      3. **Check component hygiene:**
         - `grep -rn "<button " src/ --include="*.svelte"` → should only appear inside
           `ui/` or `ai-elements/` directories, not in `domain/` or `layout/` or `routes/`
         - `grep -rn "<input " src/ --include="*.svelte"` → same rule
         - `grep -rn "<textarea " src/ --include="*.svelte"` → should not appear in `domain/`

      4. **Check message widths** in `AssistantMessage.svelte` and `UserMessage.svelte`:
         - Assistant messages: should have `max-w-[72ch]` somewhere in the chain
         - User messages: should have `max-w-[60ch]` somewhere in the chain

      5. **Check ai-elements default styles:** Open each ai-elements component that renders
         visible UI (Tool, Reasoning, Response, PromptInput) and verify their default colours
         don't clash with the warm olive palette. If they use `bg-gray-*` or `text-blue-*`
         internally, override via CSS class props.

      Fix every violation found. Document what was changed.

      **Verify:** Re-run all grep searches. Zero matches for raw Tailwind colours in app code
      (excluding `node_modules/`, `ui/`, and `ai-elements/` directories).
      Run `cd talkingcode-frontend && pnpm check`. Clean.

---

- [ ] **Step D.2: End-to-end verification**

      **What to do:**

      With both backend and frontend running, verify these scenarios:

      1. **Chat flow:**
         - Open `/` in browser
         - Empty state shows "Chat with Chidi's code" + 4 suggestion pills
         - Click a suggestion → it submits as a question
         - Planner starts (shimmer/reasoning block appears)
         - Tool calls appear inline (Tool component with status badges)
         - Response streams in (markdown rendered via Response component)
         - Response completes (streaming stops)
         - Copy action works on the message
         - "View details" opens the side panel showing plan and tools
         - Submit a second question → both messages visible in scroll thread
         - Model selector shows in composer toolbar and is functional

      2. **Repo management:**
         - Click "Repos" in nav → navigates to `/repos`
         - Page shows "Repositories" heading
         - Click "Register repo" → form appears
         - Register `chidinweke/chatGITpt` → repo card appears
         - Click "Ingest now" → shows loading, completes
         - "Last ingested" updates, history shows run
         - Click "Chat" in nav → back to chat page
         - Ask about the ingested code → should get results

      3. **Error handling:**
         - Submit a question when backend is down → error displays (not blank screen)
         - Try to ingest a non-existent repo → error message shown
         - Register with empty fields → form validation prevents submit

      **Verify:** All 3 scenarios pass. No console errors. UI consistent with design system:
      warm palette, Fraunces headings, no raw Tailwind colours.

---

- [ ] **Step D.3: Final cleanup**

      **What to do:**

      1. Run final type checks:
         - `cd /home/chidi/chatGITpt/backend && ruff check src/` — clean
         - `cd /home/chidi/chatGITpt/talkingcode-frontend && pnpm check` — clean

      2. Update `AGENTS.md` if needed:
         - Add repo management routes to the architecture description
         - Add new components to the component structure section

      3. Verify no old plan files remain:
         - `PLAN.md` — deleted
         - `backend-python-plan.md` — deleted
         - `frontend-svelte-plan.md` — deleted
         - `frontend-ui-plan.md` — deleted
         - `PLAN-ui-rebuild.md` — deleted

      4. Check for any TODO comments left in code and resolve or document them.

      **Verify:** Both type checks pass clean. `AGENTS.md` is up to date.

---

## Tests

### Backend
```bash
cd /home/chidi/chatGITpt/backend && ruff check src/
cd /home/chidi/chatGITpt/backend && python -c "from talkingcode.app import app; print('OK')"
cd /home/chidi/chatGITpt/backend && pytest tests/ -q  # if tests exist
```

### Frontend
```bash
cd /home/chidi/chatGITpt/talkingcode-frontend && pnpm check
cd /home/chidi/chatGITpt/talkingcode-frontend && pnpm test  # if tests exist
```

---

## Verification

When all steps are checked off, run this final verification:

| Check | Command / Action | Expected |
|-------|-----------------|----------|
| Backend lint | `ruff check backend/src/` | Clean |
| Backend starts | `uvicorn talkingcode.app:app` | Health OK |
| Backend OpenAPI | `curl localhost:8000/openapi.json` | 7+ routes (chat + repos) |
| Frontend types | `pnpm check` | No errors |
| Frontend dev | `pnpm dev` | Starts clean |
| Chat empty state | Visit `/` | "Chat with Chidi's code" + 4 suggestions |
| Chat flow | Submit question | Reasoning → Tools → Response stream |
| Model selector | Change model | Reflected in API call body |
| Navigation | Click Repos link | Navigates to `/repos` |
| Repo page | Visit `/repos` | "Repositories" heading renders |
| Register repo | Submit form | Repo card appears in list |
| Ingestion | Click Ingest | Completes, history shows "done" |
| Design audit | `grep bg-white src/` | Zero matches in app code |
| Visual check | Browser | Warm palette, Fraunces headings, no generic blue |
