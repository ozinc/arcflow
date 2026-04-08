# ArcFlow Starter (TypeScript)

A ready-to-go starter project for [ArcFlow](https://github.com/ozinc/arcflow) — the embedded graph database.

## Quick Start

```bash
git clone https://github.com/ozinc/arcflow-starter-ts.git
cd arcflow-starter-ts
npm install
npx tsx src/index.ts
```

## What's Included

- **src/index.ts** — Basic CRUD + graph traversal
- **src/knowledge-graph.ts** — Build a knowledge graph with entity linking
- **src/spatial.ts** — Spatial queries (WITHIN, NEAR)
- **src/algorithms.ts** — PageRank, shortest path, community detection
- **tests/** — Example tests using openInMemory()

## Key Concepts

```typescript
import { openInMemory } from 'arcflow'

const db = openInMemory()                    // No server needed
db.mutate('CREATE (n:Label {key: value})')   // Write
db.query('MATCH (n) RETURN n')               // Read
db.close()                                    // Done
```

## AI Agent Integration

```bash
# Coding agents (Claude Code, Codex, Gemini CLI) — use the CLI binary
arcflow query 'MATCH (n) RETURN count(*)'

# Cloud chat UIs (ChatGPT, Claude.ai) — use the MCP server
npx arcflow-mcp
```

## Docs

- [Get Started](https://oz.com/docs/get-started)
- [WorldCypher Reference](https://oz.com/docs/worldcypher)
- [Graph Algorithms](https://oz.com/docs/algorithms)
