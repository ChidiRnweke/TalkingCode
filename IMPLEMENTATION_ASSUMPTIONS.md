# Implementation Assumptions

This document captures assumptions made during the unsupervised implementation of TalkingCode V1.

## Tooling Approach

This implementation uses official CLI tools for project scaffolding:
- **Backend**: `uv` CLI for Python project initialization and package management (located at `backend/`)
- **Frontend**: `npx sv create` for SvelteKit project scaffolding (located at `talkingcode-frontend/`)
- **UI Components**: `shadcn-svelte` CLI for component installation

## Environment & Credentials

1. **OpenRouter API Key**: Required for planner/generation operations. Assumes user will provide `OPENROUTER_API_KEY` in environment.

2. **Database**: Uses PostgreSQL 15+ with pgVector extension. Docker Compose will provision this.

3. **GitHub Token**: Optional for file details tool - will work with cache-only mode if not provided.

4. **Default Model**: Uses OpenRouter with `anthropic/claude-3.5-sonnet` as default if no model specified.

5. **Embedding Model**: Intended model is OpenAI `text-embedding-3-small` for chunk embeddings, but end-to-end embedding generation/retrieval wiring is not fully complete yet.

## Technical Decisions

1. **Python Version**: 3.11+ for backend (modern async support, better dataclass handling).

2. **Package Management**: 
   - Backend: `uv` CLI with pyproject.toml standard
   - Frontend: `pnpm` as specified in blueprint

3. **Database Migrations**: Alembic for SQLAlchemy migrations with asyncpg driver.

4. **Testing**:
   - Backend: `pytest` with `pytest-asyncio` for async tests
   - Frontend: Vitest for unit tests, Playwright for e2e

5. **API Generation**: `openapi-typescript` for frontend type generation from backend OpenAPI spec.

## Simplifications

1. **Authentication**: V1 assumes single-user/local-dev mode. No auth layer implemented.

2. **File Details Tool**: Implements cache-only lookup as specified (no live GitHub fallback).

3. **Chunking Strategy**: Planned strategy is simple token-based chunking (~500 tokens) with overlap for V1; ingestion pipeline implementation is still incomplete.

4. **Vector Search**: Target is basic cosine similarity on pgVector without advanced reranking; current repository search path is still placeholder and must be completed.

5. **Conversation Storage**: Minimal conversation metadata (no full message history persistence beyond timeline).

## Design System

1. **Fonts**: Using system fonts as fallbacks since custom fonts (Fraunces, DM Sans) require manual setup.

2. **svelte-ai-elements**: Will install from the registry URLs specified in frontend-ui-plan.md.

## Known Limitations

1. **Payload Encryption**: `tool_call_payload_cache` table created but encryption disabled by default (stores plaintext if enabled).

2. **Tool Timeouts**: Hardcoded defaults, no dynamic adjustment based on tool characteristics.

3. **Planner Context Window**: No explicit token counting for planner context - relies on model limits.

4. **Rate Limiting**: No rate limiting implementation in V1.

## Implementation Status

**Current status (corrected):**

- [x] Step 1: Project scaffolding with uv and sv CLI
- [ ] Step 2: Backend agentic implementation (in progress)
- [ ] Step 3: Frontend architecture (in progress)
- [ ] Step 4: Frontend UI (in progress)
- [ ] Step 5: Integration and verification (not complete)

**Project Structure:**
- `backend/` - FastAPI with SQLAlchemy, planner, tools, streaming
- `talkingcode-frontend/` - SvelteKit with agentic UI
- `docker-compose.yml` - Development stack

**Key Features Partially Implemented:**
- Agentic chat loop skeleton with planner and tool execution path
- SSE whitebox event stream framework
- Structured output schema usage for classification and planning
- Timeline persistence model/repository foundations
- Reactive frontend store baseline for turn lifecycle
- Tool registry with TaskGroup-based parallel execution support

**Not Yet Ready for Full Contract Verification:**
1. Complete backend retrieval/timeline/streaming contract gaps
2. Complete frontend strict parser and contract-safe orchestration gaps
3. Run end-to-end contract verification after these gaps are closed

## Rectification Plan

- [ ] Re-baseline blueprint and assumptions documents to reflect actual state.
- [ ] Complete data ingestion/retrieval path (chunking, embeddings, pgVector query flow).
- [ ] Finish backend timeline retrieval and strict tool contract enforcement.
- [ ] Enforce strict frontend SSE payload validation (including unknown-field rejection).
- [ ] Replace placeholder/demo verification with contract-driven tests and e2e checks.

## Verification Dependencies

The verification steps assume:
- Docker daemon is running
- Ports 3000 (frontend), 8000 (backend), 5432 (postgres) are available
- At least 4GB RAM available for containers
- `uv` CLI is installed for Python project management
- `pnpm` and Node.js 20+ are available
- OPENROUTER_API_KEY and OPENAI_API_KEY are configured in backend/.env
