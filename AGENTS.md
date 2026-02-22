
# Project: TalkingCode

## Architecture

Monorepo — Pattern B (BFF): SvelteKit frontend + Python FastAPI backend.

## Stack

- Frontend: SvelteKit, pnpm, Tailwind CSS, shadcn-svelte
- Backend: Python FastAPI, async, src layout (`backend/src/talkingcode/`)
- Database: Postgres + pgVector (SQLAlchemy + Alembic)
- LLM: OpenRouter for generation (model configurable via UI), OpenAI for embeddings
- Infra: Docker Compose

## Monorepo layout

- `frontend/` — SvelteKit app (pnpm)
- `backend/` — Python FastAPI app, src layout (`backend/src/talkingcode/`)
- `docker-compose.yml` — local dev stack (postgres, backend, frontend)

## Key conventions

- Backend follows python-swe skill: Protocol interfaces, dataclass services, factory per request
- ORM types never leave the repository layer — repositories return domain models
- Services never import each other — controllers orchestrate via TaskGroup
- Frontend uses openapi-fetch with types generated from backend's OpenAPI spec
- All env vars validated at startup (AppConfig.from_env on backend)
- structlog for all backend logging

## Skills active on this project

- fullstack-swe — Architecture and monorepo structure
- python-swe — Backend architecture (services, repos, controllers, factory)
- svelte-ui — UI and design system
- feature-blueprint — Feature planning


## Design System — TalkingCode

### Status

Design system not yet established. Invoke the `svelte-ui` skill when building frontend to define:
- Color palette
- Typography scale
- Spacing tokens
- Component conventions

### Component Structure

```
frontend/src/lib/components/
├── ui/          # shadcn-svelte auto-generated base components
├── primitives/  # Themed wrappers around ui/ components
├── layout/      # Page-level structure (Sidebar, Header, MainContent)
└── domain/      # Feature-specific (ChatMessage, RepoCard, PipelineStatus)
```

### Conventions

- All components use Tailwind utility classes
- Design tokens defined in `tailwind.config.js`
- No inline styles
- shadcn-svelte for base component library
