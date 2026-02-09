# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in the AutoGPT Platform.

For repository-wide context, see the root `/CLAUDE.md`.

## Platform Overview

AutoGPT Platform is a graph-based workflow automation system for building, deploying, and managing AI agents. It consists of:

- **Backend** (`/backend`): Python FastAPI server with async support
- **Frontend** (`/frontend`): Next.js React application
- **Shared Libraries** (`/autogpt_libs`): Common Python utilities

## Quick Start

**See package-specific CLAUDE.md files for detailed commands:**
- Backend: `/backend/CLAUDE.md` - Python/Poetry commands, testing, block development
- Frontend: `/frontend/CLAUDE.md` - pnpm commands, component development, code style

**Essential commands:**

```bash
# Backend (from /backend)
poetry install && poetry run prisma migrate dev
docker compose up -d  # Start services (postgres, redis, rabbitmq, clamav)
poetry run serve      # Start backend server

# Frontend (from /frontend)
pnpm install
pnpm dev              # Start development server

# Testing
poetry run test       # Backend tests
pnpm test            # Frontend E2E tests
```

## Architecture Overview

### Backend Architecture

- **API Layer**: FastAPI with REST and WebSocket endpoints
- **Database**: PostgreSQL with Prisma ORM, includes pgvector for embeddings
- **Queue System**: RabbitMQ for async task processing
- **Execution Engine**: Separate executor service processes agent workflows
- **Authentication**: JWT-based with Supabase integration
- **Security**: Cache protection middleware prevents sensitive data caching in browsers/proxies

### Frontend Architecture

- **Framework**: Next.js App Router with React Server Components
- **State Management**: React hooks + Supabase client for real-time updates
- **Workflow Builder**: Visual graph editor using @xyflow/react
- **UI Components**: Radix UI primitives with Tailwind CSS styling
- **Feature Flags**: LaunchDarkly integration

### Key Concepts

1. **Agent Graphs**: Workflow definitions stored as JSON, executed by the backend
2. **Blocks**: Reusable components in `/backend/blocks/` that perform specific tasks
3. **Integrations**: OAuth and API connections stored per user
4. **Store**: Marketplace for sharing agent templates
5. **Virus Scanning**: ClamAV integration for file upload security

### Testing Approach

- Backend uses pytest with snapshot testing for API responses
- Test files are colocated with source files (`*_test.py`)
- Frontend uses Playwright for E2E tests
- Component testing via Storybook

### Database Schema

Key models (defined in `/backend/schema.prisma`):

- `User`: Authentication and profile data
- `AgentGraph`: Workflow definitions with version control
- `AgentGraphExecution`: Execution history and results
- `AgentNode`: Individual nodes in a workflow
- `StoreListing`: Marketplace listings for sharing agents

### Environment Configuration

#### Configuration Files

- **Backend**: `/backend/.env.default` (defaults) → `/backend/.env` (user overrides)
- **Frontend**: `/frontend/.env.default` (defaults) → `/frontend/.env` (user overrides)
- **Platform**: `/.env.default` (Supabase/shared defaults) → `/.env` (user overrides)

#### Docker Environment Loading Order

1. `.env.default` files provide base configuration (tracked in git)
2. `.env` files provide user-specific overrides (gitignored)
3. Docker Compose `environment:` sections provide service-specific overrides
4. Shell environment variables have highest precedence

#### Key Points

- All services use hardcoded defaults in docker-compose files (no `${VARIABLE}` substitutions)
- The `env_file` directive loads variables INTO containers at runtime
- Backend/Frontend services use YAML anchors for consistent configuration
- Supabase services (`db/docker/docker-compose.yml`) follow the same pattern

### Common Development Tasks

**Backend:**
- Adding blocks: See `/backend/CLAUDE.md` for Block SDK guide and development workflow
- Modifying API: Routes in `/backend/backend/server/routers/` with colocated tests
- Testing: `poetry run test` - see `/backend/CLAUDE.md` for detailed test commands

**Frontend:**
- Feature development: See `/frontend/CLAUDE.md` for component patterns and code style
- Components in `/frontend/src/components/` using shadcn/ui primitives
- API client: Regenerate with `pnpm generate:api` after backend spec changes

### Common Gotchas

- **Prisma migrations**: Always run `poetry run prisma migrate dev` after pulling schema changes
- **Port conflicts**: Default ports are 8000 (backend), 3000 (frontend), 5432 (postgres), 6379 (redis)
- **Poetry environment**: All backend Python commands MUST use `poetry run` prefix
- **Block UUIDs**: Generate with `uuid.uuid4()`, never reuse or hardcode
- **API client sync**: Run `pnpm generate:api` in frontend after backend OpenAPI spec changes
- **Block interfaces**: When creating multiple blocks, ensure inputs/outputs connect well in graph editor

### Windows-Specific Setup

**Docker Requirements:**
- Ensure Docker Desktop uses WSL2 backend (Settings → General → "Use WSL 2 based engine")
- Allocate at least 6GB RAM to Docker (Settings → Resources → Advanced)
- ClamAV virus scanning may timeout initially - container takes ~2min to fully start

**Common Windows Issues:**
- Path issues: Use Git Bash if PowerShell has problems with quoted paths
- File watching: Windows Defender may block hot-reload - add project folder to exclusions
- Line endings: Ensure Git is configured with `core.autocrlf=input` to avoid CRLF issues

### Security Implementation

**Cache Protection Middleware:**

- Located in `/backend/backend/server/middleware/security.py`
- Default behavior: Disables caching for ALL endpoints with `Cache-Control: no-store, no-cache, must-revalidate, private`
- Uses an allow list approach - only explicitly permitted paths can be cached
- Cacheable paths include: static assets (`/static/*`, `/_next/static/*`), health checks, public store pages, documentation
- Prevents sensitive data (auth tokens, API keys, user data) from being cached by browsers/proxies
- To allow caching for a new endpoint, add it to `CACHEABLE_PATHS` in the middleware
- Applied to both main API server and external API applications

### Creating Pull Requests

- Create the PR against the `dev` branch of the repository
- Ensure the branch name is descriptive (e.g., `feature/add-new-block`)
- Use conventional commit messages (see below)
- Fill out the `.github/PULL_REQUEST_TEMPLATE.md` template as the PR description
- Run the github pre-commit hooks to ensure code quality

### Reviewing/Revising Pull Requests

```bash
# Get PR reviews
gh api /repos/Significant-Gravitas/AutoGPT/pulls/{pr_number}/reviews

# Get review comments
gh api /repos/Significant-Gravitas/AutoGPT/pulls/{pr_number}/reviews/{review_id}/comments

# Get PR-specific comments
gh api /repos/Significant-Gravitas/AutoGPT/issues/{pr_number}/comments

# Get PR diff
gh pr diff {pr_number}
```

## Conventional Commits

Use this format for commit messages and Pull Request titles:

**Types:**
- `feat`: Introduces a new feature
- `fix`: Patches a bug
- `refactor`: Code change that neither fixes a bug nor adds a feature; also applies to removing features
- `ci`: Changes to CI configuration
- `docs`: Documentation-only changes
- `dx`: Improvements to developer experience

**Scopes:**
- `platform`: Changes affecting both frontend and backend
- `frontend`: Frontend-only changes
- `backend`: Backend-only changes
- `blocks`: Block modifications or additions
- `infra`: Infrastructure changes

**Sub-scopes:**
- `backend/executor`, `backend/db`
- `frontend/builder` (includes block UI component changes)
- `frontend/library`, `frontend/marketplace`
- `infra/prod`

## Quick Setup

For new development environments, use the automated installers:

```bash
# Linux/macOS
./installer/setup-autogpt.sh

# Windows (run in PowerShell as Administrator)
.\installer\setup-autogpt.bat
```

These scripts handle prerequisite checking, repo setup, and service startup.

## Key Dependencies

### Backend
- `anthropic`, `openai`, `groq`, `ollama`: LLM providers
- `mem0ai`: Memory integration for agents
- `stripe`: Payment processing for credits
- `gcloud-aio-storage`: Google Cloud Storage async support
- `firecrawl-py`: Web crawling/scraping
- `exa-py`: Exa search integration
- `tiktoken`: Token counting for LLMs
- `aioclamd`: ClamAV virus scanning (async)
- `sentry-sdk`: Error monitoring (with FastAPI, OpenAI, Anthropic, LaunchDarkly plugins)
- `launchdarkly-server-sdk`: Feature flags
- `pinecone`: Vector database
- `replicate`: AI model hosting
- `moviepy`: Video processing
- `pandas`: Data manipulation

### Frontend
- `@xyflow/react`: Visual workflow editor
- `@tanstack/react-query`: Server state management
- `@tanstack/react-table`: Advanced table management
- `react-shepherd`: Product tours/onboarding guides
- `react-hook-form` + `zod`: Form handling and validation
- `framer-motion`: Animations
- `recharts`: Data visualization
- `sonner`: Toast notifications
- `cmdk`: Command palette
- `launchdarkly-react-client-sdk`: Feature flags
- `orval`: API client generation
- `@sentry/nextjs`: Error monitoring
