# CLAUDE.md - Frontend

This file provides guidance to Claude Code when working with the frontend.

## Essential Commands

```bash
# Install dependencies
pnpm i

# Generate API client from OpenAPI spec
pnpm generate:api

# Start development server
pnpm dev

# Run E2E tests
pnpm test

# Run Storybook for component development
pnpm storybook

# Build production
pnpm build

# Format and lint
pnpm format

# Type checking
pnpm types
```

### Code Style

- Fully capitalize acronyms in symbols, e.g. `graphID`, `useBackendAPI`
- Use function declarations (not arrow functions) for components/handlers

## Architecture

- **Framework**: Next.js 15 App Router (client-first approach)
- **Data Fetching**: Type-safe generated API hooks via Orval + React Query
- **State Management**: React Query for server state, co-located UI state in components/hooks
- **Component Structure**: Separate render logic (`.tsx`) from business logic (`use*.ts` hooks)
- **Workflow Builder**: Visual graph editor using @xyflow/react
- **UI Components**: shadcn/ui (Radix UI primitives) with Tailwind CSS styling
- **Icons**: Phosphor Icons only
- **Feature Flags**: LaunchDarkly integration
- **Error Handling**: ErrorCard for render errors, toast for mutations, Sentry for exceptions
- **Testing**: Playwright for E2E, Storybook for component development

## Environment Configuration

`.env.default` (defaults) → `.env` (user overrides)

## Feature Development

See `/autogpt_platform/CONTRIBUTING.md` (if it exists) for complete patterns. Quick reference:

1. **Pages**: Create in `src/app/(platform)/feature-name/page.tsx`
   - Extract component logic into custom hooks grouped by concern, not by component. Each hook should represent a cohesive domain of functionality (e.g., useSearch, useFilters, usePagination) rather than bundling all state into one useComponentState hook.
     - Put each hook in its own `.ts` file
   - Put sub-components in local `components/` folder
   - Component props should be `type Props = { ... }` (not exported) unless it needs to be used outside the component
2. **Components**: Structure as `ComponentName/ComponentName.tsx` + `useComponentName.ts` + `helpers.ts`
   - Use design system components from `src/components/` (atoms, molecules, organisms)
   - Never use `src/components/__legacy__/*`
3. **Data fetching**: Use generated API hooks from `@/app/api/__generated__/endpoints/`
   - Regenerate with `pnpm generate:api`
   - Pattern: `use{Method}{Version}{OperationName}`
4. **Styling**: Tailwind CSS only, use design tokens, Phosphor Icons only
5. **Testing**: Add Storybook stories for new components, Playwright for E2E
6. **Code conventions**:
   - Use function declarations (not arrow functions) for components/handlers
   - Do not use `useCallback` or `useMemo` unless asked to optimise a given function
   - Do not type hook returns, let Typescript infer as much as possible
   - Never type with `any` unless a variable/attribute can ACTUALLY be of any type

## Troubleshooting

### pnpm Lockfile Conflicts

```bash
# Regenerate lockfile
rm pnpm-lock.yaml
pnpm install

# Clear pnpm cache
pnpm store prune
pnpm install
```

### Next.js Dev Server Issues

**Hot-reload not working:**
- Windows Defender may block file watching - add project folder to exclusions
- Try using turbo mode: `pnpm dev --turbo`
- Restart dev server after changing `.env` files

**Port already in use:**
```bash
# Kill process on port 3000 (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process

# Use different port
pnpm dev -- --port 3001
```

### API Client Out of Sync

```bash
# Force regenerate API client
pnpm generate:api:force

# If still failing, check backend OpenAPI spec is valid
cd ../backend
poetry run app  # Ensure backend starts without errors
```

### Playwright Test Issues

```bash
# Install browsers (may be needed on fresh Windows install)
pnpm exec playwright install

# Install browser dependencies
pnpm exec playwright install-deps

# Run tests with debug output
pnpm test:no-build --debug
```

### Windows-Specific Issues

- **Line endings**: Ensure Git uses `core.autocrlf=input` to avoid CRLF issues
- **Path length**: Enable long paths in Windows if build fails with path errors
- **File watching limits**: If hot-reload is slow, increase file watcher limit or exclude `node_modules` from antivirus
