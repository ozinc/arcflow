# ArcFlow

The operational world model layer — the persistence tier where actual world state lives. Neural world models simulate possible futures; ArcFlow records what actually happened. Spatial-temporal, confidence-scored, embedded **and** server-able. Space and time are first-class dimensions. Every node has an observation class (observed/inferred/predicted) and confidence score [0.0, 1.0]. Full GQL (ISO/IEC 39075, Cypher-compatible). Runs in-process anywhere — browser (WASM), Node.js, Python, Rust, native CLI — **or** as a long-lived local daemon over a Unix Domain Socket when multiple processes on the same machine need to share one graph + pub/sub bus.

**Eight engines. One query language. One coherent data model.** Graph storage, query execution, live streaming views, event bus, behavior engine, algorithm library, durability, and language bindings — pre-integrated. One ISO GQL dialect describes the schema, the query, the live view, the trigger, and the algorithm call. The eight layers are documented at `docs/concepts/layers/` — World Store (substrate) → Perception Lake (Bronze, reserved) → World Graph ★ (typed entity layer) → Query Engine → Live Surface → Event Bus → Behavior Engine → Algorithm Library.

## Integration model — pick the one that matches your execution context

| Consumer | Integration | Why |
|---|---|---|
| **Multi-process same-machine** (TS shell + Python workers + Rust capture all sharing one graph + pub/sub) | **`arcflow-daemon` over UDS** ★ recommended for IPC | Cross-process publish/subscribe + WAL durability, high-throughput batched publish, no port allocation. See [Daemon mode](docs/deployment/daemon.mdx). |
| **Single-process embedded** (one binary owns the graph end-to-end) | **napi-rs / WASM / C ABI in-process** | No IPC overhead at all — every operation is a function call. Browser apps, single-process daemons, embedded SDK use. |
| Claude Code, Codex, Gemini CLI | **`arcflow` CLI binary** | Shell-native, composable, no config |
| Cloud chat UIs (Claude.ai, browser agents) | **MCP server** | No local execution context, chat latency budget |
| Browser web apps that want server-pushed events | **HTTP/SSE bridge on the daemon** | Standard `EventSource` API; no extra protocol the browser doesn't already speak |
| Python / shell pipelines | **`arcflow` CLI binary** | Same as CLI agents |

**ArcFlow is optimised for true IPC-based setups** where the engine acts as a local database within a codebase on the same machine. **For any same-machine, multi-process deployment we recommend the daemon over UDS** as the default — it gives you cross-language pub/sub, WAL durability, Prometheus metrics, and SSE for browser clients out of one binary, with sub-millisecond IPC latency.

**Single-process apps still get the in-process surfaces** (WASM in the browser, napi-rs in Node, the C ABI everywhere else) when there's no second process that needs to read the graph.

**If you have a shell, use the CLI.** LLMs are trained on billions of file and shell examples. The CLI makes the world model work like the filesystem: write a `.cypher` query file, execute it, read the `.json` result. No protocol overhead, no token cost, no round-trip. The filesystem is the API.

Try it now: https://oz.com/engine — runs in your browser, no install.

One engine for graphs, vectors, full-text search, algorithms, time-series, live queries, spatial, workflows, and replication — no separate infrastructure for each.

## What ArcFlow provides

| Capability | How |
|---|---|
| Try it | **Browser — zero install** (oz.com/engine) |
| Install | `curl -fsSL https://staging.oz.com/install/arcflow \| sh` (CLI — only shipped path today; `npm install arcflow` planned RAM-C2 / 2026-Q3) |
| Server needed | **No** — in-process, like SQLite |
| Runs in browser | **Yes** (WASM) |
| Testing | `openInMemory()` — fresh graph per test, no teardown |
| Graph algorithms | `CALL algo.pageRank()` — no projection lifecycle |
| Vector search | Built-in HNSW — no separate service |
| Window functions | `LAG`, `LEAD`, `STDDEV_POP`, `PERCENT_RANK` |
| Incremental views | `CREATE LIVE VIEW` — auto-maintained, Z-set algebra |
| Virtual labels (Lakehouse-backed nodes) | `CREATE NODE LABEL Frame VIRTUAL FROM PARTITION 'lake://nfl/tracks/{season}/{week}'` — rows live in Iceberg / Parquet partitions; engine holds schema + adjacency + catalog pointer |
| Virtual computed columns | `CREATE NODE LABEL F VIRTUAL FROM PARTITION '…' COMPUTE distance_to_target = sqrt(…)` — derived properties evaluated at row-decode time, never materialized; predicates push down through the planner |
| Workspace addressing | `oz://workspace`, `oz://snapshot/<digest>`, `oz://label/<name>`, `oz://edge/<name>`, `oz://catalog`, `oz://partition/<digest>` — one URI scheme, every addressable resource |
| Storage hierarchy | Six tiers (L0 GPU VRAM → L5 object storage) + 9-state `ResidencyClass` + operator-set `TierBudget`; Memory Governor admission gate refuses over-commit, never silent-downgrades |
| CLI binary | `arcflow query '...'` — shell-native agents (Claude Code, Codex, Gemini CLI) |
| MCP server | `npx arcflow-mcp` — cloud chat UIs only (Claude.ai and similar, no local shell) |
| Typed results | Numbers are numbers, not strings |
| openCypher conformance | **100%** (3881/3881 TCK) |
| ISO GQL | **V2 native** |
| Workflow engine | **Built-in** (graph-native durable workflows) |
| Replication | **ArcFlow WAL Stream** — SWMR (single-writer, multi-reader) WAL tailing |

**When to use ArcFlow:** any system that needs a persistent, spatial-temporal, confidence-scored representation of the world — robotics perception, autonomous fleets, digital twins, AI agent infrastructure, Trusted RAG, fraud detection, game AI, knowledge graphs.

**Try before installing:** open https://oz.com/engine in your browser. Paste any Cypher or GQL query — both work. Persistent storage. Syncs to ArcFlow Cloud when ready.

## Architecture — eight layers

ArcFlow's surface decomposes into eight contract-bearing layers. The stack is bottom-to-top; each layer is documented in `docs/concepts/layers/<name>.mdx`. **ArcFlow is the hero pitch** — "the blazing-fast graph engine for modeling the real world." World Store is internal substrate; World Graph is the hero layer (★) where typed real-world entities live.

| # | Layer | What it owns | URI / surface |
|---|---|---|---|
| 1 | **World Store** | Storage substrate (internal) — Iceberg-shaped manifests, WAL segments, snapshots, content-addressed parquet blocks | `lake://bucket/path/{template}` |
| 2 | **Perception Lake** | Append-only observation landing — Bronze tier, observation-time stamped, immutable (reserved; no substrate ships today) | virtual-label scans |
| 3 | **World Graph** ★ | Typed entity layer (the hero layer) — nodes / edges / indexes / catalog; mission tiers; HLC provenance; view *over* the Store | `MATCH`, `MERGE`, `oz://workspace/...` |
| 4 | **Query Engine** | Cypher / ISO GQL parser + planner + executor; predicate pushdown, virtual-label rewriting | `EXPLAIN`, `PROFILE` |
| 5 | **Live Surface** | Standing queries + Z-set deltas + materialised views | `CREATE LIVE VIEW`, `db.subscribe()` |
| 6 | **Event Bus** | In-process pub/sub — topics, consumer groups, ack/nack, dead-letter | `CREATE TOPIC`, `PUBLISH`, `SUBSCRIBE` |
| 7 | **Behavior Engine** | Declarative behaviors, triggers, durable workflows, programs | `CREATE TRIGGER`, `CREATE PROGRAM` |
| 8 | **Algorithm Library** | Built-in graph + spatial + vector primitives; GPU-accelerated kernels | `CALL algo.*`, `CALL arcflow.*` |

The boundary between World Store (Layer 1) and World Graph (Layer 3) is a module boundary, not a process boundary — ArcFlow stays one in-process engine. World Store is named so the engine's module tree is navigable; it is **not** a sellable SKU or a separate product, and `lake://` is internal substrate addressing, not a customer-facing surface.

## Quick start

```typescript
import { open, openInMemory } from 'arcflow'

const db = openInMemory()  // No server. No setup. Just works.

// World model entity with spatial position, observation class, and confidence
db.mutate(`CREATE (e:Entity {
  name: 'Unit-01', x: 12.4, y: 8.7,
  _observation_class: 'observed', _confidence: 0.97
})`)

// Spatial: nearest entities (R*-tree backed)
const nearby = db.query(
  "CALL algo.nearestNodes(point({x: 0, y: 0}), 'Entity', 5) YIELD node, distance RETURN node.name, distance"
)
nearby.rows[0].get('name')      // "Unit-01" (string)
nearby.rows[0].get('distance')  // 15.3 (number — typed automatically)

// Parameters (prevents injection)
db.query("MATCH (e:Entity {name: $name}) RETURN e", { name: 'Unit-01' })

// Batch mutations (single write lock)
db.batchMutate([
  "MERGE (e:Entity {id: 'e1', name: 'Scout-01', _observation_class: 'observed', _confidence: 0.97})",
  "MERGE (f:Formation {id: 'f1', name: 'Alpha', pattern: 'wedge'})",
])

// Algorithms — no projection, no catalog, just call it
db.query("CALL algo.pageRank()")
db.query("CALL algo.louvain()")

// Vector search — built in, no separate service
db.mutate("CREATE VECTOR INDEX idx FOR (n:Doc) ON (n.embedding) OPTIONS {dimensions: 1536, similarity: 'cosine'}")
db.query("CALL algo.vectorSearch('idx', $vec, 10)", { vec: JSON.stringify([0.1, 0.2]) })

// Full-text search (BM25)
db.mutate("CREATE FULLTEXT INDEX ft FOR (n:Document) ON (n.content)")
db.query("CALL db.index.fulltext.queryNodes('ft', 'ownership')")

// Live subscription — fires handler with delta on each mutation
const live = db.subscribe(
  "MATCH (e:Entity) WHERE e._confidence > 0.9 AND e._observation_class = 'observed' RETURN e",
  (event) => console.log('added:', event.added, 'removed:', event.removed)
)
live.cancel()

// Paginated iteration
const cursor = db.cursor("MATCH (n:Doc) RETURN n", {}, 100)
while (!cursor.done) { const page = cursor.next() }
cursor.close()

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
  queryAt(snapshotUri: string, cypher: string, params?: QueryParams): TaggedQueryResult  // Replay against pinned snapshot
  mutate(cypher: string, params?: QueryParams): MutationResult
  batchMutate(queries: string[]): number
  isHealthy(): boolean
  stats(): { nodes: number; relationships: number; indexes: number }
  close(): void
  syncPending(): number                  // Mutations pending sync
  fingerprint(): string                  // Graph hash for sync verification
  cursor(query, params?, pageSize?): QueryCursor    // Paginated iteration
  subscribe(query, handler, options?): LiveQuery    // Live delta subscription

  // Code-intelligence fast paths (bypass the GQL compiler — JSON in, JSON out).
  // Prefer the `CodeGraph` wrapper for typed args/results; these are the raw forms.
  ingestDelta(deltaJson: string): string                              // Returns DeltaStats JSON
  impactSubgraph(rootIdsJson: string, edgeKindsJson: string, maxDepth: number): string  // Returns { nodes: [{id, hop}] } JSON

  // Virtual labels — register a Lakehouse partition pattern against a label.
  // The engine holds the schema + catalog pointer + adjacency; row data lives
  // in the Lakehouse. Returns the manifest epoch (monotonic int).
  registerVirtualPartition(label: string, partition: string): number
}

type QueryParams = Record<string, string | number | boolean | null>

interface QueryResult {
  columns: string[]
  columnTypes: ColumnType[]
  rows: TypedRow[]
  rowCount: number
  computeMs: number
  gqlstatus(): string   // "00000" = data returned, "02000" = no data (ISO GQL)
  snapshotUri: string   // arcflow://snapshot/<hex> — content-addressed snapshot URI
}

type ColumnType =
  | 'unknown' | 'null' | 'bool' | 'int' | 'float' | 'string'
  | 'nodeId' | 'relId'                                              // Entity refs — don't coerce to int
  | 'intList' | 'floatList' | 'stringList'                          // Homogeneous lists, element type known
  | 'point' | 'point3d' | 'vector3d' | 'extent' | 'lineString' | 'polygon'

interface TaggedQueryResult extends QueryResult {
  snapshotUri: string   // Always equals the URI passed to db.queryAt()
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

### Python (`arcflow` PyPI)

Python uses ctypes against the same engine binary. Surface to know about — every method here goes straight to the engine, no JSON marshalling, no subprocess hop.

```python
from arcflow import ArcFlow
from concurrent.futures import ThreadPoolExecutor
import pyarrow as pa

db = ArcFlow()                          # in-memory; ArcFlow("./data") for persistent

# Execute (typed params)
db.execute("MATCH (e:Entity {id: $id}) RETURN e.x, e.y", params={"id": 7})

# Bulk ingest — three throughput tiers
db.bulk_create_nodes([(["Entity"], {"id": i, "x": float(i)}) for i in range(95)])
db.bulk_create_relationships("OBSERVED_AT", [(eid, fid, {"x": 1.0}) for ...])
db.bulk_create_nodes_from_arrow("Entity", pa.table({"id": [...], "x": [...]}))   # Arrow-direct
db.bulk_create_relationships_from_arrow("OBSERVED_AT", pa.table({"_from": [...], "_to": [...]}))
db.load_parquet("data/tracking.parquet", "TrackingObs")                          # File-direct
db.load_csv("data/players.csv", "Player", chunk_size=100_000)

# Virtual-label registration — rows live in a Lakehouse partition; engine holds
# schema + adjacency + catalog pointer. Returns the manifest epoch.
db.execute(
    "CREATE NODE LABEL Frame (ts TIMESTAMP, x DOUBLE) "
    "VIRTUAL FROM PARTITION 'lake://nfl/tracks/{season}/{week}'"
)
# Or skip the Cypher round-trip and register directly:
epoch = db.register_virtual_partition(
    label="Frame",
    partition="lake://nfl/tracks/{season}/{week}",
)   # → int (monotonic manifest epoch)

# Virtual computed columns — derived properties evaluated at row-decode
# time by the Smart Reader; never materialised to disk. Predicates on a
# computed column push down through the planner.
db.execute("""
    CREATE NODE LABEL FrameRelToTarget VIRTUAL FROM PARTITION
      'lake://fleet/telemetry/{mission}/{day}/{shard}'
      COMPUTE
        position_relative_to_target = agent_position - target_position,
        distance_to_target = sqrt(
            (agent_position[0] - target_position[0]) ^ 2 +
            (agent_position[1] - target_position[1]) ^ 2 +
            (agent_position[2] - target_position[2]) ^ 2
        )
""")
db.execute("""
    MATCH (f:FrameRelToTarget)
    WHERE f.mission = 'survey-NW-quadrant' AND f.day = '2026-03-14'
      AND f.distance_to_target < 5.0
    RETURN f.agent_id, f.distance_to_target ORDER BY f.distance_to_target
""")

# Prepared statements (parser cached, replay with params)
stmt = db.prepare("MATCH (e:Entity {id: $eid}) RETURN e.x, e.y")
for eid in ids: row = next(iter(stmt.execute({"eid": eid})))

# Zero-copy typed result handoff
result = db.execute("MATCH (e:Entity) RETURN e.id, e.x, e.y")
tbl = result.to_arrow()                 # pyarrow.RecordBatch
df  = result.to_polars()                # polars.DataFrame  (Arrow-backed)
df  = result.to_pandas()                # pandas.DataFrame  (Arrow-backed since pandas 2)

# Deadline-over-completeness — bound the query by wall-clock budget
# (PAT-0053). Engine short-circuits at the deadline and returns the
# partial result it has so far; transport_outcome tells you whether the
# result is complete or truncated. Useful for live UX where "best
# available at deadline T" beats "wait for completeness."
result = db.execute(
    "MATCH (f:Frame) WHERE f.play_id = 1024 RETURN f LIMIT 100",
    options=arcflow.QueryOptions(deadline_ms=500),
)
result.transport_outcome          # 'truncated' | 'complete' | None
result.transport_outcome.lane     # 'cpu_scalar' | 'cpu_simd' | 'gpu_cuda' | 'gpu_metal'
result.io_stats                   # IoStats: pruning + I/O telemetry, see below

# Snapshot replay
db.query_at("MATCH (a:Account {id: 'X'}) RETURN a.balance", seq=anchor_seq)

# Live subscriptions
db.execute("CREATE LIVE VIEW high_conf AS MATCH (n) WHERE n.confidence > 0.9 RETURN n")
with db.subscribe("high_conf") as sub:
    for event in sub: handle(event["added"], event["removed"])

# CDC pull stream
changes = db.changes_since(last_seq, limit=1_000)

# Provenance
db.fingerprint()                        # graph content hash
db.snapshot_uri()                       # arcflow://snapshot/<hex>

# Threading — reads are lock-free via MVCC; writes serialise per handle.
# ctypes releases the GIL; readers fan out freely from one handle:
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(db.execute, read_queries))   # OK — reads are lock-free
# For concurrent writes, use multiple handles (db_a, db_b, ...) — see
# docs/concepts/threading-model.mdx for the HANDLE_BUSY_CONCURRENT_WRITER
# typed error + the multi-handle vs threading.Lock recovery patterns.
```

Full Python reference: [docs/bindings.mdx](docs/bindings.mdx).
Threading model + concurrent-write patterns: [docs/concepts/threading-model.mdx](docs/concepts/threading-model.mdx).

### React hooks (`@arcflow/react`)

```typescript
import { useQuery, useLiveQuery } from '@arcflow/react'

// One-shot query — re-runs when params change
const { rows, loading, error } = useQuery(db, "MATCH (e:Entity) WHERE e._confidence > 0.8 RETURN e.id, e.x, e.y", {})

// Live subscription — updates automatically on mutations
const { rows } = useLiveQuery(db, "MATCH (n:Alert) WHERE n.active = true RETURN n")
```

## Snapshot-Pinned Reads

Every snapshot has a citeable, content-addressed URI: `arcflow://snapshot/<hex>`.
Identical writes produce identical URIs across processes and machines.

| Surface | Provenance field | Pin input |
|---|---|---|
| SDK `db.query()` | `result.snapshotUri` | `db.queryAt(uri, cypher, params?)` |
| CLI `arcflow query` | `--json` envelope `__snapshot` | `--at-snapshot <uri>` |
| CLI convenience | — | `arcflow rerun --snapshot <uri> --query "..."` |
| HTTP server | headers `X-Arcflow-Snapshot-Id`, `X-Arcflow-Manifest-Pin` | `?at=<uri>` query string |
| MCP `read_query`, `graph_rag` | response envelope `snapshot_id` | optional `snapshot_uri` input |

```typescript
// Provenanced replay — bit-for-bit identical rows
const a = db.query("MATCH (e:Entity {id: 'unit-01'}) RETURN e._confidence")
const b = db.queryAt(a.snapshotUri, "MATCH (e:Entity {id: 'unit-01'}) RETURN e._confidence")
```

```bash
# CLI pin
arcflow query "MATCH (n) RETURN count(*)" --at-snapshot arcflow://snapshot/9c3b… --json
arcflow rerun --snapshot arcflow://snapshot/9c3b… --query "MATCH (n) RETURN count(*)"
```

Use case: every customer-facing answer carries the snapshot URI it observed. Surprising
result? Re-run against the same URI and either reproduce the answer (data is fixed) or
diff the URIs (data has moved).

### IoStats — pruning + I/O telemetry on every result

The `result.io_stats` envelope tells you what the engine actually read versus what it pruned. Use it to tune lakehouse layouts and verify predicate pushdown is firing.

| Field | Meaning |
|---|---|
| `bytes_read` | Total bytes read from storage for this query |
| `decoded_bytes` | Bytes after decompression — distinguishes I/O cost from CPU decode cost |
| `files_opened` | Number of parquet files actually opened |
| `partitions_pruned` | Partition directories skipped before opening any file (Hive-style pruning) |
| `partitions_scanned` | Partition directories that were walked |
| `row_groups_pruned` | Row groups skipped via parquet stats (min/max bounds) |
| `row_groups_read` | Row groups actually decoded |
| `pages_skipped` | Page-level skips via parquet page index |
| `pruning_efficiency` | `row_groups_pruned / (row_groups_pruned + row_groups_read)` — higher is better |
| `lane_used` | Compute lane that ran the query (same as `transport_outcome.lane`) |

```python
result = db.execute("MATCH (t:Trade) WHERE t.year = 2026 AND t.region = 'eu' RETURN count(*)")
result.io_stats.partitions_pruned     # 47 — other year/region combos skipped entirely
result.io_stats.row_groups_pruned     # 9201 — within scanned partitions, parquet stats skipped most
result.io_stats.pruning_efficiency    # 0.96
```

## Filesystem Projection — `arcflow project`

Write the current snapshot to a directory tree any Unix tool can read. The agent-grep
workflow: agents that speak `rg`, `grep`, `cat`, `jq` natively can now reason about the
world model with no Cypher and no MCP.

```bash
arcflow project ./world-model --json
# {"snapshot_uri":"arcflow://snapshot/9c3b…","node_count":1248,"edge_count":5821,"layout_version":1}
```

On-disk layout (deterministic, byte-identical across producers):

```
<mountpoint>/
  __snapshot.toml              # snapshot_uri + layout_version
  nodes/<Label>/<id>.json
  edges/<Type>/<id>.json
  indexes/labels.txt
  indexes/types.txt
  views/                       # reserved
```

Two projections of the same snapshot are byte-identical, so `diff -r` between
projections is a true graph-state diff.

## GQL / WorldCypher — ArcFlow's ISO GQL dialect

**Conformance:** 100% openCypher TCK (3881/3881 scenarios). Full ISO GQL V2.

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
MATCH (n:Person) AS OF seq 42 RETURN n.name
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

### ISO GQL V2 features
```cypher
-- Label predicate
MATCH (n) WHERE n IS LABELED :Person RETURN n.name

-- Element ID
MATCH (n:Person) RETURN ELEMENT_ID(n)

-- Conditional execution pipeline (NEXT chains statements)
MATCH (n:Task) WHERE n.status = 'open' RETURN count(*) AS open_count
NEXT WHEN open_count > 10 THEN
  MATCH (n:Task) WHERE n.status = 'open' SET n.priority = 'high' RETURN n
ELSE
  RETURN 'queue ok' AS message
END

-- Transaction control
START TRANSACTION
START TRANSACTION READ ONLY
START TRANSACTION READ WRITE
COMMIT
ROLLBACK

-- GQLSTATUS codes on QueryResult
-- result.gqlstatus() == "00000"  → rows returned
-- result.gqlstatus() == "02000"  → no data (empty result)
```

### Constraints
```cypher
-- UNIQUE constraint (enforced on CREATE/MERGE)
CREATE CONSTRAINT ON :Product(sku) ASSERT UNIQUE

-- PRIMARY KEY constraint (drives deterministic MERGE)
CREATE CONSTRAINT ON :Order(id) ASSERT PRIMARY KEY

-- Semantic dedup (write-time dedup with threshold)
CREATE CONSTRAINT ON :Entity(name) ASSERT SEMANTIC UNIQUE THRESHOLD 0.95
```

### Indexes
```cypher
CREATE VECTOR INDEX name FOR (n:Label) ON (n.prop) OPTIONS {dimensions: N, similarity: 'cosine'}
CREATE FULLTEXT INDEX name FOR (n:Label) ON (n.prop)
-- Composite (range) index
CREATE INDEX ON :Label(prop)
```

### Hybrid index registration

A hybrid index is a typed configuration that lets `algo.vectorSearch` consult a vector index *plus* a fulltext or property filter in one call — the planner combines the candidate sets before scoring.

```cypher
-- Register a hybrid policy: combine vector similarity with fulltext score
CALL arcflow.index.hybrid.register({
    name: 'doc_search',
    vector_index: 'doc_embed',
    fulltext_index: 'doc_body',
    weight: { vector: 0.7, fulltext: 0.3 }
}) YIELD name, created_at

CALL arcflow.index.hybrid.list()                YIELD name, vector_index, fulltext_index, weight
CALL arcflow.index.hybrid.describe('doc_search') YIELD name, config
CALL arcflow.index.hybrid.drop('doc_search')    YIELD removed
```

Once registered, `algo.vectorSearch('doc_search', $vector, 10)` consults both indexes and merges results by the declared weight.

### Partition-key column exposure

Hive-style partition keys in lakehouse paths (`lake://prod/trades/year=2026/region=eu/`) are exposed as plain properties on virtual-label nodes — queryable directly, and the planner pushes partition predicates down to the directory walk:

```cypher
CREATE NODE LABEL Trade VIRTUAL FROM PARTITION 'lake://prod/trades/'
-- year and region land as bare properties on every Trade node

MATCH (t:Trade)
WHERE t.year = 2026 AND t.region = 'eu'
RETURN count(*)
-- Engine walks only the year=2026/region=eu/ subtree; other partitions are
-- pruned before any parquet file is opened. See result.io_stats.partitions_pruned.
```

### Query hints — explicit lane selection

`HINT lane=<ident>` after a `CALL` clause overrides the planner's automatic lane selection. The chosen lane is reported back on the result envelope as `result.transport_outcome.lane`.

```cypher
CALL algo.pageRank() HINT lane=gpu_cuda YIELD nodeId, score
-- result.transport_outcome.lane → "gpu_cuda" if dispatched, or a
-- fallback lane if the hint couldn't be honored

-- Lanes: 'cpu_scalar' | 'cpu_simd' | 'gpu_cuda' | 'gpu_metal' | 'auto'
```

If the requested lane isn't available on the host (e.g., `gpu_cuda` on Apple Silicon), the engine falls back silently to the next-best lane and records the actual lane used in `transport_outcome.lane`. Use the lane field to detect silent fallbacks in tests.

### Live views (incremental computation)
```cypher
CREATE LIVE VIEW stats AS MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)
MATCH (row) FROM VIEW stats RETURN row
```

### 37 algorithms (no projection setup)
```cypher
CALL algo.pageRank()
CALL algo.louvain()
CALL algo.betweenness()
CALL algo.vectorSearch('index', $vector, 10)
CALL algo.graphRAG()
CALL algo.connectedComponents()

-- Causal reasoning (BFS over CAUSED_BY edges with cumulative confidence)
CALL arcflow.causalLineage(start_node: id(s), depth: 4)
CALL arcflow.causalPath(from: id(a), to: id(b), depth: 8)

-- Multi-source disagreement (categorical / numeric / spatial)
CALL arcflow.multi_source_disagreement(
  entity_label: "Charting", group_property: "play_id",
  source_property: "source", value_property: "run_pass",
  disagreement_kind: "categorical")

-- Trajectory analytics (sports / tracking / autonomous-vehicle telemetry)
CALL arcflow.trajectory.nearestAtFrame(entity_label: "Player",
  frame_property: "frame", x_property: "x", y_property: "y",
  frame: 1024, qx: 50.0, qy: 23.5, k: 5)
CALL arcflow.trajectory.leverageGain(...)
CALL arcflow.trajectory.releasePoint(...)
CALL arcflow.trajectory.shadowedBy(...)

-- Counterfactual branching (fork the World Graph at a WAL seq)
CALL arcflow.counterfactual.branchAt(name: 'rollout-1', seq: 42)
```

All algorithms: pageRank, confidencePageRank, betweenness, closeness, degreeCentrality,
louvain, leiden, communityDetection, connectedComponents, clusteringCoefficient,
biconnectedComponents, nodeSimilarity, triangleCount, kCore, density, diameter,
allPairsShortestPath, dijkstra, astar, nearestNodes, confidencePath, vectorSearch,
similarNodes, hybridSearch, graphRAG, graphRAGContext, graphRAGTrusted,
compoundingScore, contradictions, audienceProjection, factsByRegime, multiModalFusion,
causalLineage, causalPath, multi_source_disagreement,
trajectory.{nearestAtFrame, leverageGain, releasePoint, shadowedBy},
counterfactual.branchAt

Canonical catalog with worked examples + composition patterns: [`docs/algorithms.mdx`](/docs/algorithms).

GPU dispatch is automatic. Algorithms route to CUDA/Metal above a node-count threshold.
Multi-GPU: load-aware device selection, auto-CSR promotion, and H2D cost gate are all automatic.
Leiden requires CUDA compute capability 9.0+ (H100 and later).

On **Apple Silicon**, ArcFlow selects the optimal Metal primitive for the detected GPU
family: `simd_sum` cross-lane reductions on Apple8+, native `atomic_float` on Apple9+,
`simdgroup_matrix` tiles on M3+. CPU-side dense numerics route through Apple's
Accelerate framework (AMX/SME). Same binary across every Apple device generation;
dispatch is per-host. See [`docs/gpu.mdx`](/docs/gpu) §"Per-family kernel selection".

### Database procedures
```cypher
CALL db.stats()          -- node/rel/index counts + DenseStore/CSR stats
CALL db.schema()         -- labels, properties, relationships
CALL db.help()           -- full procedure guide
CALL db.procedures()     -- list all procedures
CALL db.demo()           -- load sample graph
CALL db.labels()         -- all node labels
CALL db.types()          -- all relationship types
CALL db.keys()           -- all property keys
CALL db.indexes()        -- all indexes
CALL db.constraints()    -- all constraints
CALL db.doctor()         -- health check and diagnostics
CALL db.export()         -- full graph snapshot as JSON
CALL db.import('<json>') -- restore from JSON snapshot
CALL db.clear()          -- drop all nodes and relationships
CALL db.validateQuery()  -- check query context validity
CALL db.fingerprint()    -- graph hash for sync verification
CALL db.clock()          -- current mutation sequence number
CALL db.changesSince(seq) -- mutations since sequence N
CALL db.liveViews()      -- list active LIVE VIEWs
CALL db.viewStats()      -- live view performance metrics
```

### Storage and performance procedures
```cypher
-- CSR (Compressed Sparse Row) cache — accelerates multi-hop traversal
CALL db.warmCsr()
  YIELD status                         -- "warm" | "rebuilt"

CALL db.csrStats()
  YIELD status, vertices, edges, rel_types, edge_type_distribution,
        memory_bytes, delta_added, delta_removed

-- DenseStore — columnar node property store (always-on)
CALL db.denseStore()
  YIELD enabled, nodes, tables, memory_bytes, coverage

-- Unified storage mode summary
CALL db.storageMode()
  YIELD mode, node_count, csr_warm, csr_auto_threshold,
        dense_store_enabled, dense_store_nodes
-- mode values: "HashMap" | "DenseStore" | "HashMap+CSR" | "DenseStore+CSR"

-- Parallel execution config
CALL db.parallelConfig()
  YIELD morsel_size, rayon_threads, dense_store_coverage, csr_status, csr_delta_pending
```

### GPU procedures
```cypher
-- Per-device GPU pool status (one row per CUDA device)
CALL db.gpuStatus()
  YIELD device_id, inflight, sm_count, vram_mib, status
-- status: "available" (inflight < 8) | "saturated"

-- Engine capability surface — GPU presence, family flags, spgemm wiring
CALL db.capabilities()
  YIELD gpu_status, gpu_spgemm, gpu_family

-- Full GPU stack info
CALL db.gpuStack()
```

### Execution context
```cypher
-- Read current context
CALL db.executionContext() YIELD context
-- context values: "local_cpu" | "local_gpu" | "distributed"

-- Set context
CALL db.setExecutionContext('local_gpu') YIELD context, status

-- Guard: errors if active context doesn't match — never silently downgrades
CALL db.requireExecutionContext('local_gpu') YIELD context, status
-- Raises EXECUTION_CONTEXT_MISMATCH if wrong
```

### OTel (observability)
```cypher
CALL db.otelPolicy() YIELD policy           -- "off" | "lite" | "full"
CALL db.setOtelPolicy('lite') YIELD policy  -- set and return new value
```

### Auth / RBAC
```cypher
CALL db.auth.whoami()                              -- current identity
CALL db.auth.policies()                            -- list all RBAC policies
CALL db.auth.check('reader', 'read', 'Person')     -- dry-run permission check
CALL db.auth.setPolicy('reader', 'read', 'Person') -- grant permission
CALL db.auth.createApiKey('service-acct', 'reader') YIELD key, name, roles
CALL db.auth.revokeApiKey('service-acct')
CALL db.auth.listApiKeys()                         YIELD name, roles, created_at
CALL db.auth.auditLog(since, limit)                YIELD identity, action, query_hash, result_code
```

### Replication
```cypher
-- SWMR (Single-Writer-Multiple-Reader) contract
CALL arcflow.replication.contract()
  YIELD mode, writes_enabled, replication_factor, description

-- WAL tailing config
CALL arcflow.replication.walTailing()
  YIELD field, value, description

-- Object-store fan-out config
CALL arcflow.replication.objectStoreFanout()
  YIELD field, value, description

-- Current replication status
CALL db.replicationStatus()
```

### Sessions (named resumable)

Named sessions survive across process restarts. Manage them via the
`arcflow session` CLI subcommand or the `auth.session.*` FFI symbols
from a language binding.

```bash
arcflow session open my-session       # open or resume
arcflow session list                  # list all open sessions
arcflow session close my-session      # close
```

### Workflow engine (graph-native)

Workflows are stored as graph nodes (`:Workflow`, `:WorkflowStep`) with `:HAS_STEP` edges. MVCC-safe. Steps are idempotent — `run()` skips already-completed steps automatically.

```cypher
-- Create workflow with steps JSON array
-- Step types: GraphQuery | GraphMutation | Sleep | ExternalCall | Condition
CALL arcflow.workflow.create('my-wf', '[{"name":"ingest","type":"GraphMutation"},{"name":"analyze","type":"GraphQuery"}]')
  YIELD workflow_id, name, status   -- status: "pending"

-- List all workflows
CALL arcflow.workflow.list()
  YIELD workflow_id, name, status

-- Run / progress a workflow (auto-advances pending steps; skips completed)
CALL arcflow.workflow.run('my-wf')
  YIELD workflow_id, name, started_steps

-- Cancel a workflow (all pending/running steps → cancelled)
CALL arcflow.workflow.cancel('my-wf')
  YIELD workflow_id, name, status

-- Retry a failed or cancelled step (resets to pending)
CALL arcflow.workflow.retryStep(wf_id, 'step-name')
  YIELD step_id, step_name, status

-- Reference procedures (return schema docs, not runtime state)
CALL arcflow.workflow.stepKinds()     YIELD kind, description, retryable, durable
CALL arcflow.workflow.memoizedResult(wf_id, step_name) YIELD key, value
CALL arcflow.workflow.retryPolicy()   YIELD field, value, description
CALL arcflow.workflow.flowControl()   YIELD mode, description, scope, unit
CALL arcflow.workflow.eventTypes()    YIELD step_type, trigger, correlation_key, timeout_supported
CALL arcflow.workflow.errorPolicy()   YIELD field, value, description
CALL arcflow.workflow.cancelPolicy()  YIELD rule, description
CALL arcflow.workflow.cronPolicy()    YIELD field, value, description
CALL arcflow.workflow.delayPolicy()   YIELD field, value, description
CALL arcflow.workflow.sleepPolicy()   YIELD field, value, description
```

### OpenUSD scene procedures
```cypher
-- Export entire graph as USD ASCII
CALL arcflow.scene.toUsda() YIELD usda

-- Resolve a USD prim path to a graph node ID
CALL arcflow.scene.primId('/World/MyMesh') YIELD prim_path, prim_id

-- Frustum cull (6-plane containment)
-- Args: origin (ox,oy,oz), direction (dx,dy,dz), fovDeg, nearZ, farZ
CALL arcflow.scene.frustumQuery(0, 0, 0, 1, 0, 0, 60, 1, 100)
  YIELD node_id, label, x, y, z

-- Line-of-sight between two node IDs
CALL arcflow.scene.lineOfSight(from_id, to_id) YIELD has_los, note

-- Collision contacts for a node
CALL arcflow.scene.collisions(node_id) YIELD from_id, to_id, impulse, at_time

-- Neighborhood query in local coordinate space
CALL arcflow.scene.queryInLocalSpace(node_id, 10.0)
  YIELD node_id, local_x, local_y, local_z
```

### OpenClaw (plugin/gateway)
```cypher
CALL arcflow.claw.pluginContracts()  YIELD field, type, required, description
CALL arcflow.claw.gatewayMethods()   YIELD method, description
CALL arcflow.claw.latencyPolicy()    YIELD tier, max_latency_ms, description, hot_path_excluded
CALL arcflow.claw.workerModel()      YIELD mode, description, latency_class, isolation
```

### Skills (named, callable units)
```gql
-- Prompt-backed skill — text in, text out
CREATE SKILL summarize FROM PROMPT 'Summarize the following: {{input}}'

-- LLM-tier skill with explicit per-skill model routing
CREATE SKILL coach_summary
    FROM PROMPT 'Analyze {{name}}'
    ALLOWED ON [Player]
    TIER LLM
    MODEL 'cli/claude-code'        -- catalog row, see arcflow.llm.catalog()

-- Bundle export / import (skill packs are portable JSON blobs)
CALL arcflow.skills.export('my-pack', '1.0.0') YIELD json
CALL arcflow.skills.import(json)               YIELD name, version, skill_count
```

The `MODEL` clause routes the LLM call to a specific catalog row instead of the default `oz/deepseek-v3`. Combined with the CLI-provider substrate, this makes `cli/claude-code`, `cli/codex`, `cli/gemini` reachable from customer Cypher.

### Account login (optional — for hosted features)
```bash
# Browser-based login — opens oz.com/world/login and listens on a local
# callback port. Credentials are written to ~/.arcflow/credentials.json
# (chmod 0600 on Unix).
arcflow login
arcflow login --token <TOKEN>     # headless / CI mode — no browser
arcflow whoami                    # prints email + tier; --json for envelope
arcflow logout                    # clears credentials
```

Local-only use does not require login. Login unlocks first-party hosted features (the `oz/*` LLM provider catalog, hosted skill packs, account-tier limits). Everything else — graph storage, queries, live views, BYOK LLM providers — works fully offline.

### LLM Node — provider keys, sidecar, budgets
```bash
# Provider API key management — keys live in the OS keychain (macOS Keychain,
# Linux Secret Service, Windows Credential Manager). Never written to disk.
arcflow keys add openai     # interactive, or:
arcflow keys add openai --from-stdin
arcflow keys list           # provider, masked_key, daily_cap_usd, set_at
arcflow keys rm openai
arcflow keys set-daily-cap openai 25.00
```

```cypher
-- Discover available models (oz first-party + your BYOK providers)
CALL arcflow.llm.catalog() YIELD model, provider, context_window, input_usd_per_million, output_usd_per_million

-- Inspect BudgetMeter state (per-key daily-cap enforcement)
CALL arcflow.llm.budget() YIELD provider, day, spent_usd, cap_usd, remaining_usd
```

**Architecture:** an LLM call from Cypher (`TIER LLM` skill) routes through an `arcflow-llm` sidecar process, which the runtime supervises. The sidecar holds provider state and isolates LLM call failures from the engine. The supervisor restarts the sidecar on crash. BudgetMeter intercepts every call and rejects on cap-exceeded with a typed error.

**Providers:**
- **`openai/*`** — OpenAI-compatible HTTPS provider; works for OpenAI, Together, Groq, Anyscale, any vendor that exposes the same API shape
- **`cli/*`** — SubprocessCli provider; routes to a locally-installed CLI agent (`claude-code`, `codex`, `gemini`); zero network egress
- **`oz/*`** — first-party catalog hosted at `llm.oz.com` (BYO-token or hosted billing)

### Triggers (event-driven skill firing)
```gql
-- Bind a skill to a graph event
CREATE TRIGGER detect_on_frame
    ON :ImageFrame WHEN CREATED
    RUN SKILL detect_objects

-- WHEN CREATED | MODIFIED | DELETED
DROP TRIGGER detect_on_frame

-- Per-property granularity — only fire on writes that change `bbox`
CREATE TRIGGER bbox_changed
    ON :Detection.bbox WHEN MODIFIED
    RUN SKILL recompute_overlap

-- Inspect registered triggers
CALL db.triggers() YIELD name, label, property, event, skill, created_at
```

The optional `.property` after the label restricts the trigger to writes that actually change that property — useful when many properties change per node but only one downstream computation cares about a specific field.

### Programs (installable capability manifests)
```gql
-- Declare a capability with hardware requirements, I/O schema, and executor wiring
CREATE PROGRAM yolo_v11 VERSION '1.0' (
    PROVIDES ['object_detection', 'ball_tracking'],
    CARDINALITY PER_SENSOR,            -- SINGLETON | PER_SENSOR | SHARDED BY <prop>
    INPUT  :ImageFrame { bytes BYTES, width INT, height INT },
    OUTPUT :Detection  { label STRING, confidence FLOAT, bbox FLOAT[] },
    REQUIRES GPU (SM >= 7.0, VRAM >= 4.0),
    MODEL '/models/yolov11x.onnx',
    EXECUTOR unix:///tmp/yolo.sock HEARTBEAT 5000,
    EVIDENCE NEURAL,                   -- SYMBOLIC | WASM | LLM | NEURAL
    SKILLS [detect_objects],
    TRIGGERS [ON :ImageFrame WHEN CREATED]
)

DROP PROGRAM yolo_v11

-- Program procedure API
CALL arcflow.programs.list()                         YIELD name, version, provides, cardinality
CALL arcflow.programs.describe('yolo_v11')           YIELD input_schema, output_schema, hardware_reqs
CALL arcflow.programs.validate('yolo_v11')           YIELD passed, details
CALL arcflow.programs.health('yolo_v11')             YIELD status, last_heartbeat_ms
CALL arcflow.programs.find_by_capability('ball_3d')  YIELD name
CALL arcflow.programs.install($manifest)             YIELD name, installed_at
CALL arcflow.programs.remove('yolo_v11')             YIELD removed
```

### Ontology (IS_A hierarchy)
```cypher
CALL arcflow.ontology.subtypes('Agent')   YIELD label, depth
CALL arcflow.ontology.ancestors('Person') YIELD label, depth
```

### Contributor readiness
```cypher
CALL arcflow.contributor.starterIssues()    YIELD title, difficulty, crate, estimated_hours
CALL arcflow.contributor.maintainerScore()  YIELD dimension, score, threshold, status
```

### Spatial (R*-tree, exact)
```cypher
-- K-nearest neighbor
CALL algo.nearestNodes(point({x: 10.0, y: 10.0}), 'Player', 5)
  YIELD node, distance RETURN node.name, distance

-- Radius search (compiler pushes distance() into R*-tree via SpatialIndexScan)
MATCH (r:Robot) WHERE distance(r.position, point({x: 0, y: 0})) < 50.0 RETURN r.name

-- Bounding box
MATCH (e:Entity)
WHERE e.position.x >= 0 AND e.position.x <= 100
  AND e.position.y >= 0 AND e.position.y <= 50
RETURN e.name

-- Frustum / visibility (6-plane containment, index-narrowed)
CALL algo.objectsInFrustum($frustum) YIELD node, distance RETURN node.name, distance

-- Raycast (line-of-sight)
CALL spatial.raycast(point({x: 0, y: 0, z: 2}), point({x: 1, y: 0, z: 0}), 100.0)
  YIELD hit, distance RETURN hit.name, distance

-- Live geofencing (fires within 20ms of position update — edge-triggered, not level-triggered)
CREATE LIVE VIEW zone_alpha AS
  MATCH (p:Player)
  WHERE p.position.x >= 30 AND p.position.x <= 70
    AND p.position.y >= 30 AND p.position.y <= 70
  RETURN p.name, p.position

LIVE MATCH (p:Player)
WHERE distance(p.position, point({x: 50, y: 50})) < 25.0
RETURN p.name, p.position

-- Spatial + graph fused (DAG: spatial prefilter and CSR traversal run concurrently)
CALL algo.nearestNodes(order.location, 'Warehouse', 5) YIELD node AS wh, distance
MATCH (wh)-[:SUPPLIES]->(item:Item {sku: $sku}) WHERE item.stock > 0
RETURN wh.name, distance, item.stock ORDER BY distance

-- Coordinate frame metadata
CALL db.spatialMetadata() YIELD crs, meters_per_unit, up_axis, handedness, calibration_version

-- Dispatch observability (lane_chosen: CpuLive | CpuBatch | GpuLocal | GpuMulti)
CALL arcflow.spatial.dispatch_stats()
  YIELD lane_chosen, estimated_candidates, actual_candidates,
        prefilter_us, rtree_us, gpu_transfer_us, kernel_us, total_us

-- Live trigger metrics
CALL arcflow.spatial.trigger_stats()
  YIELD query_name, node_id, predicate_type, evaluation_us, fired
```

Index is dynamic — inserts/updates/deletes are O(log N), no rebuild. Coarse grid pre-filter reduces candidate set ~95% before R*-tree evaluation. Bulk ingest (USD prims) uses Sort-Tile-Recursive packing — 500K prims in under 1 second.

### Live Queries
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

### Workflow (durable multi-step pipeline)
```typescript
// Create and run a 3-step pipeline
db.execute("CALL arcflow.workflow.create('etl', '[{\"name\":\"extract\",\"type\":\"GraphQuery\"},{\"name\":\"transform\",\"type\":\"GraphMutation\"},{\"name\":\"load\",\"type\":\"GraphMutation\"}]')")
db.execute("CALL arcflow.workflow.run('etl')")

// Retry a failed step
db.execute("CALL arcflow.workflow.list()")  // get workflow_id
db.execute("CALL arcflow.workflow.retryStep(42, 'transform')")
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
| `UNKNOWN_FUNCTION` | validation | Run `CALL db.help()` |
| `UNKNOWN_PROCEDURE` | validation | Run `CALL db.procedures()` |
| `DB_CLOSED` | integration | Don't query after `db.close()` |
| `WORKFLOW_NOT_FOUND` | validation | Run `CALL arcflow.workflow.list` |
| `STEP_NOT_FOUND` | validation | Check step name in workflow |
| `EXECUTION_CONTEXT_MISMATCH` | integration | Run `CALL db.setExecutionContext(...)` first |

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
sdk/src/                        # SDK source
  index.ts, types.ts, errors.ts        # Core API
  code-intelligence.ts                 # Code graph layer (CodeGraph, Labels, Edges)
sdk/tests/                      # SDK tests (Vitest)
mcp/                                   # MCP server (npx arcflow-mcp)
docs/                                  # MDX docs — full reference
  concepts/world-model.mdx             # World Model concept: spatial-temporal, observed/inferred/predicted
  guides/world-model.mdx               # Step-by-step: entities, spatial queries, temporal replay, live monitoring
  use-cases/autonomous-systems.mdx     # Robot fleets, UAVs, shared world model
  use-cases/digital-twins.mdx          # Live spatial replica of physical facilities
  use-cases/robotics.mdx               # Sensor fusion pipeline, track lifecycle, ROS bridge
  guides/swarm-agents.mdx              # AI agent swarms on a shared world model
  guides/rag-pipeline.mdx              # Trusted RAG: confidence-filtered retrieval
  guides/code-intelligence.mdx         # Code intelligence guide
examples/                              # Runnable examples
fixtures/                              # Sample datasets
install/                               # Install script
LICENSE                                # MIT (this repo's contents)
```

## Extended reference

See `llms-full.txt` for complete WorldCypher syntax with every pattern and procedure.
