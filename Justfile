# ArcFlow SDK — Task runner
# Install just: https://github.com/casey/just

# Default: show available commands
default:
    @just --list

# ── Build ──

# Build the TypeScript SDK (ESM + CJS + types)
build:
    cd typescript && npm run build

# Type-check without emitting
typecheck:
    cd typescript && npm run typecheck

# ── Test ──

# Run all tests
test:
    cd typescript && ARCFLOW_METAL_FORCE_UNAVAILABLE=true npm test

# Run tests in watch mode
test-watch:
    cd typescript && ARCFLOW_METAL_FORCE_UNAVAILABLE=true npm run test:watch

# ── Lint ──

# Check code style
lint:
    cd typescript && npm run lint

# Auto-fix code style
lint-fix:
    cd typescript && npm run lint:fix

# Format code
format:
    cd typescript && npm run format

# ── Release ──

# Add a changeset
changeset:
    cd typescript && npx changeset

# Publish to npm
release:
    cd typescript && npm run build && npx changeset publish

# ── Development ──

# Install dependencies
install:
    cd typescript && npm install

# Clean build artifacts
clean:
    rm -rf typescript/dist typescript/node_modules

# Full check (build + typecheck + lint + test)
check: build typecheck lint test
