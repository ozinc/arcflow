# ArcFlow

The embedded graph database. Runs in the browser, Node.js, Python, Rust, and Docker. No server needed.

**[Try it now — arcflow.dev/engine](https://arcflow.dev/engine)** — runs in your browser, zero install.

```bash
npm install arcflow
```

```typescript
import { openInMemory } from 'arcflow'

const db = openInMemory()  // No server. No Docker. No connection string.
db.mutate("CREATE (n:Person {name: 'Alice', age: 30})")
const result = db.query("MATCH (n:Person) RETURN n.name, n.age")
console.log(result.rows[0].get('name'))  // "Alice"
console.log(result.rows[0].get('age'))   // 30 (typed)
db.close()
```

Two lines to a working graph. Or zero lines — just open the browser.

## Why ArcFlow

One in-process library replaces six services:

| You'd otherwise need | ArcFlow has it built in |
|---|---|
| Neo4j (graph DB) | Cypher-compatible graph store |
| Redis (cache) | In-memory, zero-copy |
| DuckDB (analytics) | Window functions, aggregations |
| Pinecone (vector DB) | HNSW vector index |
| Elasticsearch (search) | BM25 full-text search |
| Temporal (workflows) | Graph-native durable workflows |

### vs. Neo4j / Memgraph

| | ArcFlow | Neo4j / Memgraph |
|---|---|---|
| Try it | **[Browser — zero install](https://arcflow.dev/engine)** | Download + install + configure |
| Install | `npm install arcflow` | Docker + driver + connection |
| First query | 2 lines | 10+ lines |
| Server needed | **No** — in-process | Yes — separate process |
| Runs in browser | **Yes** (WASM) | No |
| Testing | `openInMemory()` | Docker container + teardown |
| Algorithms | `CALL algo.pageRank()` | GDS: project → catalog → run → drop |
| Vector search | Built-in | Separate service |
| Window functions | LAG, LEAD, STDDEV_POP, PERCENT_RANK | Not available |
| Live views | `CREATE LIVE VIEW` — auto-maintained | Not available |
| MCP server | `npx arcflow-mcp` | None |

## What you can build

| Use Case | Why ArcFlow |
|---|---|
| Knowledge graphs | Entity linking, confidence-scored facts, provenance — all in one engine |
| RAG pipelines | Vector search + graph traversal + full-text in a single query |
| AI agent memory | In-process graph the agent can spin up, use, and discard |
| Trading pipelines | Window functions, live views, proven batch/delta equivalence |
| Sports analytics | Spatial queries, player tracking, real-time algorithms |
| Game state | Behavior trees as graph subgraphs, persistent world model |
| IoT / robotics | Sensor state, spatial awareness, temporal snapshots |

## Features

```typescript
// 30+ algorithms — no projection, no catalog
db.query("CALL algo.pageRank()")
db.query("CALL algo.louvain()")

// Vector search — no separate service
db.mutate("CREATE VECTOR INDEX idx FOR (n:Doc) ON (n.embedding) OPTIONS {dimensions: 1536, similarity: 'cosine'}")
db.query("CALL algo.vectorSearch('idx', $vec, 10)", { vec: JSON.stringify(embedding) })

// Full-text search — BM25
db.mutate("CREATE FULLTEXT INDEX ft FOR (n:Person) ON (n.name)")
db.query("CALL db.index.fulltext.queryNodes('ft', 'Alice')")

// Window functions
db.query("MATCH (n:Bar) RETURN lag(n.close, 1) OVER (PARTITION BY n.symbol ORDER BY n.date)")

// Live views — incremental, auto-maintained
db.mutate("CREATE LIVE VIEW stats AS MATCH (n) RETURN labels(n), count(*)")

// Temporal snapshots
db.query("MATCH (n:Person) AS OF 1700000000 RETURN n.name")

// Persistence — WAL-journaled
const db = open('./data/graph')

// Structured errors — not stack traces
try { db.query("BAD") } catch (e) {
  e.code       // "EXPECTED_KEYWORD"
  e.suggestion // "Expected MATCH or CREATE"
}
```

## Install

| Method | Command | Friction |
|---|---|---|
| Browser | [arcflow.dev/engine](https://arcflow.dev/engine) | Zero — click and go |
| npm | `npm install arcflow` | One command |
| Binary | `curl -fsSL https://github.com/ozinc/arcflow/releases/latest/download/install.sh \| sh` | curl + run |
| Python | `pip install arcflow` | One command |
| Rust | `cargo add arcflow` | One command |
| Docker | `docker run ghcr.io/ozinc/arcflow:latest` | Container |
| MCP (AI agents) | `npx arcflow-mcp` | One command |

## Documentation

| Section | What you'll learn |
|---|---|
| [Quickstart](docs/quickstart.mdx) | First query in 5 minutes |
| [WorldCypher](docs/worldcypher/index.mdx) | Query language reference |
| [Tutorials](docs/tutorials/knowledge-graph.mdx) | Knowledge graph, vector search, algorithms |
| [Recipes](docs/recipes/crud.mdx) | Copy-paste patterns |
| [API Reference](docs/reference/api.mdx) | TypeScript SDK API |
| [Compatibility](docs/reference/compatibility.mdx) | Full feature matrix |

## For AI coding agents

| File | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Full context — API, WorldCypher, comparison table, patterns |
| [`llms.txt`](llms.txt) | Compact reference for quick orientation |
| [`llms-full.txt`](llms-full.txt) | Complete reference with every procedure |

## License

MIT
