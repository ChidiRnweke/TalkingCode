# Implementation Assumptions

This document captures assumptions made during the unsupervised implementation of TalkingCode V1.

## Tooling Approach

This implementation uses official CLI tools for project scaffolding:
- **Backend**: `uv` CLI for Python project initialization and package management (located at `backend/`)
- **Frontend**: `npx sv create` for SvelteKit project scaffolding (located at `talkingcode-frontend/`)
- **UI Components**: `shadcn-svelte` CLI for component installation

## Environment & Credentials

1. **OpenRouter API Key**: Required for LLM operations (planner, classification, embeddings). Assumes user will provide `OPENROUTER_API_KEY` in environment.

2. **Database**: Uses PostgreSQL 15+ with pgVector extension. Docker Compose will provision this.

3. **GitHub Token**: Optional for file details tool - will work with cache-only mode if not provided.

4. **Default Model**: Uses OpenRouter with `anthropic/claude-3.5-sonnet` as default if no model specified.

5. **Embedding Model**: Uses OpenAI `text-embedding-3-small` for chunk embeddings.

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

3. **Chunking Strategy**: Uses simple token-based chunking (~500 tokens) with overlap for V1.

4. **Vector Search**: Basic cosine similarity on pgVector without advanced reranking.

5. **Conversation Storage**: Minimal conversation metadata (no full message history persistence beyond timeline).

## Design System

1. **Fonts**: Using system fonts as fallbacks since custom fonts (Fraunces, DM Sans) require manual setup.

2. **svelte-ai-elements**: Will install from the registry URLs specified in frontend-ui-plan.md.

## Known Limitations

1. **Payload Encryption**: `tool_call_payload_cache` table created but encryption disabled by default (stores plaintext if enabled).

2. **Tool Timeouts**: Hardcoded defaults, no dynamic adjustment based on tool characteristics.

3. **Planner Context Window**: No explicit token counting for planner context - relies on model limits.

4. **Rate Limiting**: No rate limiting implementation in V1.

## Verification Dependencies

The verification steps assume:
- Docker daemon is running
- Ports 3000 (frontend), 8000 (backend), 5432 (postgres) are available
- At least 4GB RAM available for containers
- `uv` CLI is installed for Python project management
- `pnpm` and Node.js 20+ are available
