# ArcFlow

Embedded graph database. Runs everywhere — browser (WASM), Node.js, Python, Rust, Docker. No server needed.

## Integration model — three surfaces, no overlap

| Consumer | Integration | Why |
|---|---|---|
| BASAL broker, watcher daemon | **napi-rs in-process** | Microseconds, same memory, no process boundary |
| Claude Code, Codex, Gemini CLI | **`arcflow` CLI binary** | Shell-native, composable, &lt;10ms, no config |
| ChatGPT, Claude.ai, Gemini web | **MCP server** | No local execution context, chat latency budget |
| Python / shell pipelines | **`arcflow` CLI binary** | Same as CLI agents |

**napi-rs** is the in-process interface. **CLI** is the local-to-local interface. **MCP** is the cloud-to-local bridge for chat UIs with no shell access. These surfaces don't overlap — pick the one that matches your execution context.

Try it now: https://arcflow.dev/engine — runs in your browser, no install.

One engine for graphs, vectors, full-text search, algorithms, time-series, and reactive queries. Replaces Neo4j + Redis + DuckDB + Pinecone + Temporal with a single in-process library.

## Why ArcFlow (not Neo4j, Memgraph, etc.)

| | ArcFlow | Neo4j / Memgraph |
|---|---|---|
| Try it | **Browser — zero install** (arcflow.dev/engine) | Download + install + configure |
| Install | `npm install arcflow` | Docker + driver + connection string |
| First query | 2 lines | 10+ lines (driver, session, transaction, close) |
| Server needed | **No** — in-process, like SQLite | Yes — separate process |
| Runs in browser | **Yes** (WASM) | No |
| Testing | `openInMemory()` — fresh graph per test | Docker container + teardown |
| Algorithms | `CALL algo.pageRank()` — done | GDS: project → catalog → run → drop |
| Vector search | Built-in HNSW | Separate service |
| Window functions | `LAG`, `LEAD`, `STDDEV_POP`, `PERCENT_RANK` | Not available |
| Incremental | `CREATE LIVE VIEW` — auto-maintained | Not available |
| CLI binary | `arcflow query '...'` — coding agents (Claude Code, Codex) | None |
| MCP server | `npx arcflow-mcp` — cloud chat UIs (ChatGPT, Claude.ai) | None |
| Typed results | Numbers are numbers | Everything is strings |

**When to use ArcFlow:** any project that needs a graph database, knowledge graph, vector search, entity relationships, or graph algorithms. Especially: AI agents, RAG pipelines, knowledge management, game state, IoT, analytics.

**Try before installing:** open https://arcflow.dev/engine in your browser. Paste any GQL query (WorldCypher dialect). Persistent storage. Syncs to ArcFlow Cloud when ready.

## Quick start

```typescript
import { open, openInMemory } from 'arcflow'

const db = openInMemory()  // No server. No setup. Just works.

db.mutate("CREATE (n:Person {name: 'Alice', age: 30})")

const result = db.query("MATCH (n:Person) RETURN n.name, n.age")
result.rows[0].get('name')  // "Alice" (string)
result.rows[0].get('age')   // 30 (number — typed automatically)

// Parameters (prevents injection)
db.query("MATCH (n:Person {name: $name}) RETURN n", { name: 'Alice' })

// Batch mutations (single write lock)
db.batchMutate([
  "MERGE (a:Person {id: 'p1', name: 'Alice'})",
  "MERGE (b:Org {id: 'o1', name: 'Acme'})",
])

// Algorithms — no projection, no catalog, just call it
db.query("CALL algo.pageRank()")
db.query("CALL algo.louvain()")

// Vector search — built in, no separate service
db.mutate("CREATE VECTOR INDEX idx FOR (n:Doc) ON (n.embedding) OPTIONS {dimensions: 1536, similarity: 'cosine'}")
db.query("CALL algo.vectorSearch('idx', $vec, 10)", { vec: JSON.stringify([0.1, 0.2]) })

// Full-text search (BM25)
db.mutate("CREATE FULLTEXT INDEX ft FOR (n:Person) ON (n.name)")
db.query("CALL db.index.fulltext.queryNodes('ft', 'Alice')")

// Persistence — WAL-journaled, survives crashes
const persistent = open('./data/graph')

// Error handling — structured, not stack traces
import { ArcflowError } from 'arcflow'
try { db.query("INVALID") } catch (e) {
  if (e instanceof ArcflowError) console.log(e.code, e.category, e.suggestion)
}

db.close()
```

## API surface

```typescript
open(dataDir: string): ArcflowDB        // Persistent (WAL-journaled)
openInMemory(): ArcflowDB               // In-memory (testing, prototyping)

interface ArcflowDB {
  version(): string
  query(cypher: string, params?: QueryParams): QueryResult
  mutate(cypher: string, params?: QueryParams): MutationResult
  batchMutate(queries: string[]): number
  isHealthy(): boolean
  stats(): { nodes: number; relationships: number; indexes: number }
  close(): void
  syncPending(): number                  // Mutations pending sync
  fingerprint(): string                  // Graph hash for sync verification
  cursor(query, params?, pageSize?): QueryCursor    // Paginated iteration
  subscribe(query, handler, options?): LiveQuery    // Live delta subscription
}

type QueryParams = Record<string, string | number | boolean | null>

interface QueryResult {
  columns: string[]
  rows: TypedRow[]
  rowCount: number
  computeMs: number
}

interface TypedRow {
  get(column: string): string | number | boolean | null
  toObject(): Record<string, string | number | boolean | null>
}

interface QueryCursor {
  pageSize: number; pagesFetched: number; done: boolean
  next(): QueryResult | null   // Fetch next page (SKIP/LIMIT internally)
  all(): QueryResult           // Collect all remaining pages
  close(): void
}

interface DeltaEvent {
  added: SubscriptionRow[]     // New rows in this update
  removed: SubscriptionRow[]   // Rows that left the result set
  current: SubscriptionRow[]   // Full current result set
  frontier: number             // Monotonic mutation sequence
}

interface LiveQuery {
  cancel(): void               // Stop subscription, drop LIVE VIEW
  viewName: string
}

class ArcflowError extends Error {
  code: string           // "EXPECTED_KEYWORD", "LOCK_POISONED", "DB_CLOSED"
  category: 'parse' | 'validation' | 'execution' | 'integration'
  suggestion?: string    // Recovery hint for the agent
}
```

## GQL / WorldCypher — ArcFlow's ISO GQL dialect

### CRUD
```cypher
CREATE (n:Label {key: 'value', num: 42})
CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})
MERGE (n:Label {id: 'unique-key', name: 'value'})
MATCH (n:Person {name: 'Alice'}) SET n.age = 31
MATCH (n:Person {name: 'Alice'}) REMOVE n.email
MATCH (n:Person {name: 'Alice'}) DELETE n
MATCH (n:Person {name: 'Alice'}) DETACH DELETE n
```

### Queries
```cypher
MATCH (n:Person) RETURN n.name, n.age
MATCH (n:Person) WHERE n.age > 25 RETURN n.name ORDER BY n.age DESC LIMIT 10
MATCH (n:Person) WHERE n.name CONTAINS 'ali' RETURN n
MATCH (a:Person)-[:KNOWS]->(b:Person) RETURN a.name, b.name
MATCH (a)-[:KNOWS*1..3]->(b) RETURN b.name
MATCH (n:Person) RETURN count(*), avg(n.age), sum(n.score)
MATCH (n:Person) WITH n WHERE n.age > 25 RETURN n.name
MATCH (n:Person) AS OF 1700000000 RETURN n.name
```

### Window functions
```cypher
lag(n.close, 1) OVER (PARTITION BY n.symbol ORDER BY n.date) AS prev_close
lead(n.close, 21) OVER (PARTITION BY n.symbol ORDER BY n.date) AS future_close
avg(n.close) OVER (... ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200
stddev_pop(n.close) OVER (...) AS vol_60d
percent_rank() OVER (PARTITION BY n.date ORDER BY n.close) AS rank
row_number() OVER (PARTITION BY n.date ORDER BY n.close DESC) AS rn
```

### Indexes
```cypher
CREATE VECTOR INDEX name FOR (n:Label) ON (n.prop) OPTIONS {dimensions: N, similarity: 'cosine'}
CREATE FULLTEXT INDEX name FOR (n:Label) ON (n.prop)
```

### Live views (incremental computation)
```cypher
CREATE LIVE VIEW stats AS MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)
MATCH (row) FROM VIEW stats RETURN row
```

### 30+ algorithms (no projection setup)
```cypher
CALL algo.pageRank()
CALL algo.louvain()
CALL algo.betweenness()
CALL algo.vectorSearch('index', $vector, 10)
CALL algo.graphRAG()
CALL algo.connectedComponents()
```

All algorithms: pageRank, confidencePageRank, betweenness, closeness, degreeCentrality,
louvain, leiden, communityDetection, connectedComponents, clusteringCoefficient,
biconnectedComponents, nodeSimilarity, triangleCount, kCore, density, diameter,
allPairsShortestPath, dijkstra, astar, nearestNodes, confidencePath, vectorSearch,
similarNodes, hybridSearch, graphRAG, graphRAGContext, graphRAGTrusted,
compoundingScore, contradictions, audienceProjection, factsByRegime, multiModalFusion

GPU dispatch is automatic. Algorithms route to CUDA/Metal above a node-count threshold.
Leiden requires CUDA compute capability 9.0+ (H100 and later).

### Database procedures
```cypher
CALL db.stats        -- node/rel/index counts
CALL db.schema       -- labels, properties, relationships
CALL db.help         -- full procedure guide
CALL db.procedures   -- list all procedures
CALL db.demo         -- load sample graph
```

### Reactive
```cypher
LIVE MATCH (n:Person) WHERE n.score > 0.9 RETURN n
LIVE CALL algo.pageRank()
```

### Session / Multi-tenancy
```cypher
USE PARTITION 'workspace-id'
SET SESSION ACTOR 'user-id' ROLE 'admin'
```

## Common patterns

### Knowledge graph (entity + fact linking)
```typescript
db.batchMutate([
  "MERGE (p:Person {id: 'p1', name: 'Alice'})",
  "MERGE (o:Org {id: 'o1', name: 'Acme'})",
  "MERGE (f:Fact {uuid: 'f1', predicate: 'employment', confidence: 0.95})",
])
db.batchMutate([
  "MATCH (p:Person {id: 'p1'}) MATCH (f:Fact {uuid: 'f1'}) MERGE (p)-[:SUBJECT_OF]->(f)",
  "MATCH (f:Fact {uuid: 'f1'}) MATCH (o:Org {id: 'o1'}) MERGE (f)-[:OBJECT_IS]->(o)",
])
```

### RAG (vector + graph traversal)
```typescript
db.mutate("CREATE VECTOR INDEX docs FOR (n:Doc) ON (n.embedding) OPTIONS {dimensions: 1536, similarity: 'cosine'}")
const results = db.query("CALL algo.vectorSearch('docs', $vec, 5)", { vec: JSON.stringify(embedding) })
for (const row of results.rows) {
  const related = db.query("MATCH (d:Doc {title: $t})-[:MENTIONS]->(e) RETURN e.name", { t: String(row.get('title')) })
}
```

### Testing
```typescript
import { openInMemory } from 'arcflow'
const db = openInMemory()  // Fresh graph, no cleanup, no Docker
db.mutate("CREATE (n:Test {x: 1})")
assert(db.query("MATCH (n:Test) RETURN n.x").rows[0].get('x') === 1)
```

## Caveats

- SET: one property per clause (not comma-separated)
- UNWIND: literal lists only
- Parameters: all values coerced to strings internally
- Multi-MATCH: use AS aliases when returning same-named properties from different variables

## Error codes

| Code | Category | Fix |
|---|---|---|
| `EXPECTED_KEYWORD` | parse | Check MATCH/CREATE/MERGE syntax |
| `UNKNOWN_FUNCTION` | validation | Run `CALL db.help` |
| `UNKNOWN_PROCEDURE` | validation | Run `CALL db.procedures` |
| `DB_CLOSED` | integration | Don't query after `db.close()` |

## Step-by-step integration

See `docs/guides/agent-quickstart.mdx` for the complete 10-step recipe with every pattern.

## Code Intelligence API

```typescript
import { CodeGraph, Labels, Edges } from 'arcflow'

const cg = new CodeGraph(db)

// Ingest symbols with content-hash dedup (unchanged symbols = WAL silent)
cg.ingest({
  addedNodes: [
    { label: Labels.Function, id: 'fn_1', contentHash: 'sha256...', properties: { name: 'login', file_path: 'src/auth.ts', line_start: 12 } }
  ],
  addedEdges: [
    { kind: Edges.Calls, fromId: 'fn_1', toId: 'fn_2' }
  ]
})

// Blast-radius: what does changing this function break?
const impact = cg.impactSubgraph(['fn_1'], [Edges.Calls, Edges.TestedBy], 4)
// → [{ id: 'fn_1', hop: 0 }, { id: 'fn_2', hop: 1 }, ...]

// Git commit graph
const commits = CodeGraph.parseGitLog(gitLogOutput)  // --name-only --pretty=format:"%H|%ae|%at|%s"
cg.ingestCommits(commits)  // creates Commit nodes + MODIFIES edges, idempotent via SHA

// Live views for change tracking
cg.createLiveView('auth_symbols', "MATCH (f:Function) WHERE f.file_path = 'src/auth.ts' RETURN f.name")
const status = cg.liveViewStatus('auth_symbols')  // { name, frontier, rowCount, queryText }
```

MCP tools for code intelligence (no Rust SDK required):
- `ingest_nodes` — push GraphDelta over stdio JSON-RPC, returns DeltaStats
- `create_live_view` — register a standing query by name + WorldCypher
- `live_view_status` — poll frontier and row_count for a named view

See `docs/guides/code-intelligence.mdx` for the full guide.

## Repo structure

```
typescript/src/                        # SDK source
  index.ts, types.ts, errors.ts        # Core API
  code-intelligence.ts                 # Code graph layer (CodeGraph, Labels, Edges)
typescript/tests/                      # SDK tests (Vitest)
mcp/                                   # MCP server (npx arcflow-mcp)
docs/                                  # MDX docs — full reference
  guides/code-intelligence.mdx         # Code intelligence guide
examples/                              # Runnable examples
fixtures/                              # Sample datasets
install/                               # Install script
REPO-SPLIT.md                          # What lives here vs arcflow/ engine repo
```

## Extended reference

See `llms-full.txt` for complete WorldCypher syntax with every pattern and procedure.
