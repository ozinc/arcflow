# Contributing

Thanks for your interest in contributing to the ArcFlow SDK!

## Development setup

```bash
git clone https://github.com/ArcFlowLabs/arcflow-sdk.git
cd arcflow-sdk/typescript
npm install
npm run build
npm test
```

### Prerequisites

- Node.js 18+
- npm 9+
- A pre-built `@arcflow/core` native binary (or `ARCFLOW_METAL_FORCE_UNAVAILABLE=true` for testing)

## Project structure

```
typescript/
├── src/
│   ├── index.ts      # SDK entry point (open, openInMemory, ArcflowDB)
│   ├── types.ts      # TypeScript interfaces
│   └── errors.ts     # ArcflowError class
├── tests/
│   └── sdk.test.ts   # Vitest tests
├── tsup.config.ts    # Build config (ESM + CJS dual output)
├── vitest.config.ts  # Test config
└── biome.json        # Linter + formatter config
```

## Commands

| Command | Description |
|---|---|
| `npm run build` | Build with tsup (ESM + CJS + types) |
| `npm test` | Run tests with Vitest |
| `npm run test:watch` | Run tests in watch mode |
| `npm run lint` | Check with Biome |
| `npm run lint:fix` | Auto-fix lint issues |
| `npm run format` | Format with Biome |
| `npm run typecheck` | Type-check without emitting |

## Making changes

1. Fork the repo and create a branch
2. Make your changes
3. Run `npm run lint:fix && npm run typecheck && npm test`
4. Add a changeset: `npx changeset`
5. Open a PR

## Adding documentation

Docs live in `docs/` as markdown. They are the single source of truth — the website renders them.

- **Getting started** → `docs/getting-started/`
- **Core concepts** → `docs/core-concepts/`
- **Tutorials** → `docs/tutorials/`
- **Recipes** → `docs/recipes/`
- **Reference** → `docs/reference/`
- **Use cases** → `docs/use-cases/`

## Adding examples

Examples live in `examples/` as runnable TypeScript files. Every example must:
- Import from `@arcflow/sdk`
- Use `openInMemory()` by default (no filesystem dependency)
- Be self-contained (no external dependencies)
- Include console output showing expected results

## Changesets

We use [changesets](https://github.com/changesets/changesets) for versioning. Every PR that changes SDK behavior should include a changeset:

```bash
npx changeset
```

## Code style

- Biome handles formatting and linting — run `npm run lint:fix` before committing
- No semicolons, single quotes, tabs
- Prefer explicit types over inference at API boundaries
- Keep it simple — the SDK is a thin wrapper, not a framework
