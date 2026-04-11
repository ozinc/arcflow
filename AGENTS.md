# ArcFlow

The World Model database — spatial-temporal, confidence-scored, embedded. Space and time are first-class dimensions. Every node has an observation class (observed/inferred/predicted) and confidence score [0.0, 1.0]. Full GQL (ISO/IEC 39075, Cypher-compatible). Runs everywhere — browser (WASM), Node.js, Python, Rust, Docker. No server needed.

## Integration model — three surfaces, no overlap

| Consumer | Integration | Why |
|---|---|---|
| Application daemons, broker processes | **napi-rs in-process** | Microseconds, same memory, no process boundary |
| Claude Code, Codex, Gemini CLI | **`arcflow` CLI binary** | Shell-native, composable, <10ms, no config |
| ChatGPT, Claude.ai, Gemini web | **MCP server** | No local execution context, chat latency budget |
| Python / shell pipelines | **`arcflow` CLI binary** | Same as CLI agents |

**napi-rs** is the in-process interface. **CLI** is the local-to-local interface. **MCP** is the cloud-to-local bridge for chat UIs with no shell access. These surfaces don't overlap — pick the one that matches your execution context.

Try it now: https://oz.com/engine — runs in your browser, no install.

One engine for graphs, vectors, full-text search, algorithms, time-series, live queries, spatial, workflows, and replication — no separate infrastructure for each.

## What ArcFlow provides

| Capability | How |
|---|---|
| Try it | **Browser — zero install** (oz.com/engine) |
| Install | `npm install arcflow` |
| Server needed | **No** — in-process, like SQLite |
| Runs in browser | **Yes** (WASM) |
| Testing | `openInMemory()` — fresh graph per test, no teardown |
| Graph algorithms | `CALL algo.pageRank()` — no projection lifecycle |
| Vector search | Built-in HNSW — no separate service |
| Window functions | `LAG`, `LEAD`, `STDDEV_POP`, `PERCENT_RANK` |
| Incremental views | `CREATE LIVE VIEW` — auto-maintained, Z-set algebra |
| CLI binary | `arcflow query '...'` — shell-native agents (Claude Code, Codex, Gemini CLI) |
| MCP server | `npx arcflow-mcp` — cloud chat UIs only (ChatGPT, Claude.ai, Gemini web) |
| Typed results | Numbers are numbers, not strings |
| openCypher conformance | **100%** (3881/3881 TCK) |
| ISO GQL | **V2 native** |
| Workflow engine | **Built-in** (graph-native durable workflows) |
| Replication | **Arrow Flight WAL tailing** (SWMR) |

**When to use ArcFlow:** any system that needs a persistent, spatial-temporal, confidence-scored representation of the world — robotics perception, autonomous fleets, digital twins, AI agent infrastructure, Trusted RAG, fraud detection, game AI, knowledge graphs.

**Try before installing:** open https://oz.com/engine in your browser. Paste any Cypher or GQL query — both work. Persistent storage. Syncs to ArcFlow Cloud when ready.

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
  gqlstatus(): string   // "00000" = data returned, "02000" = no data (ISO GQL)
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

### React hooks (`@arcflow/react`)

```typescript
import { useQuery, useLiveQuery } from '@arcflow/react'

// One-shot query — re-runs when params change
const { rows, loading, error } = useQuery(db, "MATCH (e:Entity) WHERE e._confidence > 0.8 RETURN e.id, e.x, e.y", {})

// Live subscription — updates automatically on mutations
const { rows } = useLiveQuery(db, "MATCH (n:Alert) WHERE n.active = true RETURN n")
```

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

### Live views (incremental computation)
```cypher
CREATE LIVE VIEW stats AS MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)
MATCH (row) FROM VIEW stats RETURN row
```

### 27 algorithms (no projection setup)
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
Multi-GPU: load-aware device selection, auto-CSR promotion, and H2D cost gate are all automatic.
Leiden requires CUDA compute capability 9.0+ (H100 and later).

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

-- GPU kernel dispatch registry — H2D cost gate and minimum requirements
CALL dbms.gpuThresholds()
  YIELD algorithm, min_input_size, bytes_per_element, validated, cuda_min_cc

-- Full GPU stack info
CALL db.gpuStack()
```

### Execution context (ANTI-0019)
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

-- Arrow Flight WAL tailing config
CALL arcflow.replication.walTailing()
  YIELD field, value, description

-- Object-store fan-out config
CALL arcflow.replication.objectStoreFanout()
  YIELD field, value, description

-- Current replication status
CALL db.replicationStatus()
```

### Sessions (named resumable)
```cypher
-- Open a named session (survives reconnects within the process)
CALL arcflow.session.open('my-session')
  YIELD name, session_id, status

-- List all open sessions
CALL arcflow.session.list()
  YIELD name, session_id, query_count, created_at

-- Close a session
CALL arcflow.session.close('my-session')
  YIELD name, status   -- status: "closed" | "not_found"
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

### Skills (bundle export/import)
```cypher
CALL arcflow.skills.export('my-pack', '1.0.0') YIELD json
CALL arcflow.skills.import(json)               YIELD name, version, skill_count
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

-- Frustum / visibility (6-plane containment, < 2ms for 50 entities / 10 frusta)
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
typescript/src/                        # SDK source
  index.ts, types.ts, errors.ts        # Core API
  code-intelligence.ts                 # Code graph layer (CodeGraph, Labels, Edges)
typescript/tests/                      # SDK tests (Vitest)
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
REPO-SPLIT.md                          # What lives here vs arcflow/ engine repo
```

## Extended reference

See `llms-full.txt` for complete WorldCypher syntax with every pattern and procedure.
