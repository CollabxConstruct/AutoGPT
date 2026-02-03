# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in the AutoGPT Platform.

For repository-wide context, see the root `/CLAUDE.md`.

## Platform Overview

AutoGPT Platform is a graph-based workflow automation system for building, deploying, and managing AI agents. It consists of:

- **Backend** (`/backend`): Python FastAPI server with async support
- **Frontend** (`/frontend`): Next.js React application
- **Shared Libraries** (`/autogpt_libs`): Common Python utilities

## Essential Commands

### Backend Development

```bash
# Install dependencies
cd backend && poetry install

# Run database migrations
poetry run prisma migrate dev

# Start all services (database, redis, rabbitmq, clamav)
docker compose up -d

# Run the backend server
poetry run serve

# Run tests
poetry run test

# Run specific test
poetry run pytest path/to/test_file.py::test_function_name

# Run block tests (tests that validate all blocks work correctly)
poetry run pytest backend/blocks/test/test_block.py -xvs

# Run tests for a specific block (e.g., GetCurrentTimeBlock)
poetry run pytest 'backend/blocks/test/test_block.py::test_available_blocks[GetCurrentTimeBlock]' -xvs

# Lint and format
# prefer format if you want to just "fix" it and only get the errors that can't be autofixed
poetry run format  # Black + isort
poetry run lint    # ruff
```

More details can be found in TESTING.md

#### Creating/Updating Snapshots

When you first write a test or when the expected output changes:

```bash
poetry run pytest path/to/test.py --snapshot-update
```

⚠️ **Important**: Always review snapshot changes before committing! Use `git diff` to verify the changes are expected.

### Frontend Development

```bash
# Install dependencies
cd frontend && npm install

# Start development server
npm run dev

# Run E2E tests
npm run test

# Run Storybook for component development
npm run storybook

# Build production
npm run build

# Type checking
npm run types
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

**Adding a new block:**

1. Create new file in `/backend/backend/blocks/`
2. Inherit from `Block` base class
3. Define input/output schemas
4. Implement `run` method
5. Register in block registry
6. Generate the block uuid using `uuid.uuid4()`

Note: when making many new blocks analyze the interfaces for each of these blcoks and picture if they would go well together in a graph based editor or would they struggle to connect productively?
ex: do the inputs and outputs tie well together?

**Modifying the API:**

1. Update route in `/backend/backend/server/routers/`
2. Add/update Pydantic models in same directory
3. Write tests alongside the route file
4. Run `poetry run test` to verify

**Frontend feature development:**

1. Components go in `/frontend/src/components/`
2. Use existing UI components from `/frontend/src/components/ui/`
3. Add Storybook stories for new components
4. Test with Playwright if user-facing

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

- Create the PR aginst the `dev` branch of the repository.
- Ensure the branch name is descriptive (e.g., `feature/add-new-block`)/
- Use conventional commit messages (see below)/
- Fill out the .github/PULL_REQUEST_TEMPLATE.md template as the PR description/
- Run the github pre-commit hooks to ensure code quality.

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
