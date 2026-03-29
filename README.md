# ArcFlow

The spatial-temporal graph database. One engine for graphs, vectors, time, space, and algorithms.

## Install

```bash
npm install arcflow
```

Three paths to hello world:

| Path | Time | Command |
|---|---|---|
| Docker | 30s | `docker run -p 7687:7687 ghcr.io/oz-global/arcflow:latest` |
| Binary | 60s | `curl -fsSL https://arcflow.dev/install \| sh && arcflow` |
| SDK | 2 min | `npm install arcflow` then 5 lines of TypeScript |

## See it work

```typescript
import { openInMemory } from 'arcflow'

const db = openInMemory()

db.mutate("CREATE (alice:Person {name: 'Alice', age: 30})")
db.mutate("CREATE (bob:Person {name: 'Bob', age: 35})")
db.mutate("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")

const result = db.query("MATCH (n:Person) RETURN n.name, n.age ORDER BY n.name")
for (const row of result.rows) {
  console.log(row.get('name'), row.get('age'))
}
// Alice 30
// Bob 35

db.query("CALL algo.pageRank()")   // Graph algorithms — no setup
db.close()
```

## What you can build

| Use Case | Example | Query Flavor |
|---|---|---|
| Knowledge graphs | Entity extraction, fact linking, confidence scoring | `MATCH (a)-[:SUBJECT_OF]->(f:Fact) WHERE f.confidence > 0.9` |
| RAG pipelines | Vector + graph + full-text retrieval for LLMs | `CALL algo.vectorSearch('docs', $vec, 10)` |
| Sports analytics | Track players, compute formations, detect events | `MATCH (p:Player) WHERE p.speed > 5.0 RETURN p.name` |
| Fleet/logistics | Vehicle routing, geofencing, ETA prediction | `MATCH (v:Vehicle)-[:ON_ROUTE]->(r) RETURN v.pos` |
| IoT/robotics | Sensor networks, spatial awareness, path planning | `MATCH (s:Sensor) AS OF $timestamp RETURN s.reading` |
| AI agents | Give LLMs spatial reasoning via MCP | `arcflow-mcp --data-dir ./graph` |
| Gaming/simulation | NPC awareness, world state, behavior trees | `MATCH (npc:NPC)-[:CAN_SEE]->(target) RETURN target` |

## Features

- **30+ graph algorithms** — PageRank, Louvain, betweenness, connected components, k-core
- **Vector search** — HNSW index, cosine/euclidean similarity, hybrid search
- **Full-text search** — BM25-scored indexes
- **Temporal queries** — `AS OF` snapshots, time windows, trajectory tracking
- **Reactive queries** — `LIVE MATCH`, `LIVE CALL`, persistent live views
- **WAL persistence** — crash-safe with automatic recovery
- **GPU acceleration** — Metal (macOS) and CUDA (Linux) for graph operations
- **Typed results** — numbers, booleans, and nulls as native types
- **Structured errors** — codes, categories, and recovery suggestions

## Documentation

| Section | What you'll learn |
|---|---|
| [Quickstart](docs/getting-started/quickstart.md) | First query in 5 minutes |
| [Installation](docs/getting-started/installation.md) | npm, Docker, binary, local dev |
| [WorldCypher](docs/core-concepts/worldcypher.md) | Query language reference |
| [Tutorials](docs/tutorials/knowledge-graph.md) | Build a knowledge graph, vector search, algorithms |
| [Recipes](docs/recipes/crud.md) | Copy-paste patterns for common operations |
| [API Reference](docs/reference/api.md) | Complete TypeScript SDK API |
| [Compatibility](docs/reference/compatibility.md) | Full WorldCypher feature matrix |

## SDKs

| Language | Package | Status |
|---|---|---|
| TypeScript | `npm install arcflow` | Stable |
| Python | `pip install arcflow` | Available |
| Rust | `arcflow = "x.y"` | Available |
| C/C++ | `libarcflow.h` / `arcflow.hpp` | Available |
| Docker | `ghcr.io/oz-global/arcflow` | Available |
| MCP | `arcflow-mcp` | Available |

## For AI coding agents

This repo is optimized for agent consumption. All agent context lives in neutral, tool-agnostic files:

| File | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Full context: API, WorldCypher reference, repo structure |
| [`llms.txt`](llms.txt) | Compact reference (quick orientation) |
| [`llms-full.txt`](llms-full.txt) | Complete reference (every pattern and procedure) |

## API at a glance

```typescript
import { open, openInMemory, ArcflowError } from 'arcflow'

const db = openInMemory()                              // or open('./data')
db.query(cypher, params?)                              // → QueryResult
db.mutate(cypher, params?)                             // → MutationResult
db.batchMutate(queries[])                              // → number
db.query("CALL algo.pageRank()")                       // 30+ algorithms
db.query("CALL algo.vectorSearch('idx', $vec, 10)")    // Vector search
db.stats()                                             // { nodes, relationships, indexes }
db.isHealthy()                                         // boolean
db.close()
```

## Development

```bash
just install    # Install dependencies
just build      # Build (ESM + CJS + types)
just test       # Run tests
just check      # Build + typecheck + lint + test
```

## License

MIT
