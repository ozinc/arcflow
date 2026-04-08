# ArcFlow Data Pipeline Case Study

A single TypeScript file replacing dbt, Great Expectations, Airflow, a lineage tracker, a BI
drill tool, and snapshot tables — with nothing but an embedded graph database.

```
dbt              → batchMutate() + GQL SET for delta
Great Expectations → CREATE LIVE VIEW — fires on every write, zero polling
Airflow          → Stage nodes + FEEDS edges + PipelineRun ledger
Lineage tracker  → SOURCED_FROM edges — provenance on every record
BI drill tool    → graph traversal: result → record → source document
Snapshot tables  → AS OF seq N — WAL is the timeline
```

Run it:

```bash
node index.cjs
```

---

## What only ArcFlow can do

Before anything else: here are three things this example demonstrates that no other database
— graph or relational — can match.

### 1. Data quality that is always on, not scheduled

Every other DQ framework (Great Expectations, dbt tests, Monte Carlo) runs on a schedule.
You run a batch job. You wait. You find out a constraint was violated hours after the data
arrived.

In ArcFlow, you write the constraint once:

```cypher
CREATE LIVE VIEW dq_zero_price AS
  MATCH (r:Record) WHERE r.price < 0.01 RETURN r.id
```

That view fires **on every single write**, incrementally, in the same process, in under a
millisecond. Not a cron job. Not a checkpoint runner. Not a Spark job. The engine evaluates
only what changed — powered by Z-set algebra, which gives a mathematical proof that the
incremental result is identical to a full re-scan.

```typescript
// After any batchMutate() call:
const violations = db.query("MATCH (row) FROM VIEW dq_zero_price RETURN row").rowCount
// → 1 if any record has price < 0.01, updated instantly, no polling
```

This is backed by ISO GQL semantics (`CREATE LIVE VIEW` is a GQL-native construct) and
Z-set batch↔delta equivalence (PAT-0021). No competitor — not Neo4j, not Ultipa, not
Spanner, not DuckDB — has reactive standing queries on a graph with provable equivalence.

### 2. Drill-through from a broken metric to its source in one query

In every traditional BI stack, when a metric looks wrong you open four dashboards, ping the
data engineering team, and wait. The lineage tool is a separate service. The compute layer is
another service. Getting from "this aggregate is wrong" to "this is the source file that
caused it" requires crossing service boundaries manually.

In ArcFlow, provenance is edges. The drill-through is one traversal:

```cypher
MATCH (r:Record)-[:SOURCED_FROM]->(d:Document)
WHERE r.confidence < 0.8 AND r.invalidatedAt IS NULL
RETURN r.id, r.confidence, d.path
ORDER BY r.confidence
```

No LLM. No lineage service. No separate catalog. You write provenance edges when you ingest
(section 2 of this example), and drill-through is a free consequence.

### 3. Blast-radius analysis without a lineage tool

When a source file changes — say `data/sales-Q2.csv` is redelivered with corrections —
which downstream records need to be reprocessed? In a traditional stack this requires a
lineage catalog (Amundsen, DataHub, OpenLineage) to be kept in sync with your pipeline.

In ArcFlow the `CONTAINS` edges you created at ingest ARE the lineage:

```cypher
MATCH (d:Document {id:'doc_002'})-[:CONTAINS]->(r:Record)
RETURN r.id, r.category
```

No external catalog. No sync job. No staleness. The lineage is part of the graph, versioned
by the same WAL as the data.

---

## Why graph-native pipelines?

Traditional pipelines treat data as tables and lineage as an afterthought — a separate
service, a separate schema, a separate team. When a metric looks wrong, you open five
dashboards, fire Slack messages, and eventually someone re-runs a query manually.

ArcFlow stores data, lineage, quality results, and the pipeline DAG itself in the same
graph. Drill-through from a broken aggregate to its source document is one GQL query.
There is no separate lineage infrastructure to maintain.

---

## Concepts demonstrated

### 1. Single code definition for batch, delta, and frozen queries

The same `MATCH (r:Record) WHERE r.price < 0.01 RETURN r.id` expression is used in three
different evaluation modes without rewriting anything:

| Mode | ArcFlow API | When to use |
|---|---|---|
| **Batch** | `db.query(...)` | Full scan at run time |
| **Live / incremental** | `CREATE LIVE VIEW v AS MATCH ...` | Real-time DQ — fires on every write |
| **Frozen snapshot** | `MATCH ... AS OF seq N` | Point-in-time audit at WAL sequence N |
| **Cursor (streaming)** | `db.cursor(query, params, pageSize)` | Large result sets, page-by-page |

This is what "single code definition" means in practice: write the predicate once, choose the
execution mode at the call site. In a dbt + Airflow stack you'd write the same logic three
times across three different systems, in three different languages.

**How it works:** ArcFlow's Z-set delta engine compiles each query into a plan that can be
evaluated either as a full scan (`evaluate_plan()`) or as an incremental update over a
signed-weight delta (`evaluate_plan_delta()`). A LIVE VIEW registers the plan; the engine
re-evaluates only the delta on each mutation — no polling, no re-scan.

**Frozen snapshots** use the WAL (write-ahead log) as the timeline. Every committed mutation
has a sequence number. `AS OF seq N` replays the WAL up to sequence N and returns the graph
at that exact point. No snapshot tables, no CDC tables, no time-travel infrastructure.

### 2. Automated Data Quality — the Great Expectations pattern, engine-native

```typescript
// Register the expectation BEFORE ingesting data
db.mutate(`CREATE LIVE VIEW dq_zero_price AS
  MATCH (r:Record) WHERE r.price < 0.01
  RETURN r.id AS id`)

// After any write, check the violation count
const violations = db.query("MATCH (row) FROM VIEW dq_zero_price RETURN row").rowCount
```

Live views fire on every GQL write — `CREATE`, `MERGE`, `SET`, `DETACH DELETE`. The
rowCount is a reliable "any violations exist" signal for new writes. For current violation
state after `SET` operations, run a direct query (Z-set delta propagates additions; property-
change-driven removals are tracked as a planned extension).

**Supported predicates in live views:** `=`, `>`, `<`, `IS NULL`. For `IN` list checks and
range operators (`>=`, `<=`, `<>`), use a direct query after each write — it's one line.

**What this replaces:** Great Expectations requires a Python runtime, a checkpoint runner, a
separate result store, and a scheduling layer. ArcFlow DQ is in-process, sub-millisecond, and
requires no infrastructure.

### 3. Prune — soft-delete + hard-delete with provenance intact

Pipelines accumulate stale records: superseded versions, failed loads, records that fail
late-arriving validation. ArcFlow handles both soft-delete (mark invalidated) and hard-delete
(DETACH DELETE) natively.

```cypher
-- Soft-delete: mark invalidated, keep for audit
MATCH (r:Record {id:'r004'}) SET r.invalidatedAt = 1700200000, r.invalidReason = 'unknown_category'

-- Hard-delete: remove from graph + all edges
MATCH (r:Record) WHERE r.invalidatedAt > 0 DETACH DELETE r
```

After a hard-delete, `dq_no_source` and other live views immediately stop tracking the
removed records. No stale violation counts.

### 4. Auto DAG and pipeline documentation

The pipeline DAG is not a YAML file or a Python decorator — it's nodes in the graph:

```cypher
MATCH (a:Stage)-[:FEEDS]->(b:Stage)
RETURN a.label AS from, b.label AS to
ORDER BY a.id
```

This means the DAG is queryable, versioned (WAL), and directly linked to run history and
stage timing. Critical-path analysis (`MATCH path = (a:Stage)-[:FEEDS*]->(b:Stage) RETURN length(path)`)
requires no separate tool.

The `PipelineRun` node records every execution. Stage timing is stored as `lastRunMs` on each
Stage node, so `MATCH (run:PipelineRun)-[:EXECUTED]->(s:Stage) RETURN s.label, s.lastRunMs`
gives a full audit trail without a separate logging system.

### 5. Drill-through and reconciliation — the historical BI gap

This is the most underappreciated use case. The gap: a metric is wrong. You can't trace back
why — your lineage tool is separate from your compute layer, so you toggle between four
dashboards and fire Slack messages.

ArcFlow closes this gap with provenance edges on every record at ingest time:

```cypher
-- Record points back to its source document
MATCH (r:Record {id:'r005'})-[:SOURCED_FROM]->(d:Document)
RETURN r.id, r.confidence, d.path
```

When an expectation fails, the drill-through is automatic:

```cypher
MATCH (r:Record)-[:SOURCED_FROM]->(d:Document)
WHERE r.confidence < 0.8 AND r.invalidatedAt IS NULL
RETURN r.id, r.confidence, d.path
ORDER BY r.confidence
```

No LLM. No separate lineage service. The graph traversal IS the drill-through.

**Why this was historically a BI gap:** Relational databases store data in tables. Lineage
lives in a metadata catalog (Amundsen, DataHub, Atlas) — a separate service. When you need
to join a broken metric to its source, you cross a service boundary, and the join is manual.
Graph-native storage makes lineage first-class: the `SOURCED_FROM` edge is just another
traversal step.

### 6. Expectation testing — not just assertions

Great Expectations treats expectations as boolean assertions. ArcFlow treats them as standing
queries — which means expectations can have rich semantics:

```cypher
-- Not just "avg confidence >= 0.8" but "which category is dragging it down?"
MATCH (r:Record) WHERE r.invalidatedAt IS NULL
RETURN r.category, avg(r.confidence) AS cat_avg
ORDER BY cat_avg

-- And which source document is responsible?
MATCH (r:Record)-[:SOURCED_FROM]->(d:Document)
WHERE r.confidence < 0.8 AND r.invalidatedAt IS NULL
RETURN d.path, count(*) AS failing_records, avg(r.confidence) AS avg_conf
ORDER BY failing_records DESC
```

This was previously "ML-specific" because building this kind of rich diagnostic capability
required custom Python: pandas groupby, matplotlib, a Jupyter notebook per expectation.
ArcFlow makes it GQL — the same language used for everything else.

### 7. Content-hash dedup — WAL-silent idempotent ingestion

For high-frequency delta loads, re-ingesting unchanged records wastes WAL bandwidth and
triggers unnecessary live view re-evaluation. ArcFlow's `apply_node_edge_delta()` primitive
supports content-hash dedup at the engine level:

```typescript
cg.ingest({
  addedNodes: [
    // Second ingest of same hash: WAL silent, zero bytes written
    { label: 'DemoRecord', id: 'x001', contentHash: 'hash_v1', properties: { price: 120.50 } },
    { label: 'DemoRecord', id: 'x001', contentHash: 'hash_v1', properties: { price: 120.50 } }, // skipped
    // Hash changed: written
    { label: 'DemoRecord', id: 'x001', contentHash: 'hash_v2', properties: { price: 121.00 } }, // updated
  ]
})
// → { nodesAdded: 1, nodesUpdated: 1, nodesSkippedByHash: 1 }
```

The content hash is a SHA-256 of the record's source bytes (computed by your ingestion code,
not the engine). This makes the ingestion pipeline idempotent: re-running a failed batch
produces the same graph state.

**Trade-off:** `ingestDelta()` bypasses the GQL compiler — no CDC, no live view updates.
Use `batchMutate()` when live DQ views need to fire. Use `ingestDelta()` for maximum
throughput on content-hash-deduplicated data (53× batch INSERT vs GQL).

---

## Hidden features that optimize this use case

These are less obvious ArcFlow capabilities that directly accelerate data pipeline work:

### Z-set arrangement sharing

When multiple LIVE VIEWs join on the same key (e.g., `r.source`), the engine shares a single
BTreeMap-indexed arrangement across all views. 100 DQ checks on the same fact table cost
roughly 1.5× the memory of one check, not 100×. Register all views before ingesting data.

### Incremental graph algorithms

Graph algorithms (BFS, PageRank, degree centrality) update incrementally when edges change:
- Edge add/remove triggers O(affected-nodes) re-evaluation, not full re-compute
- Triangle count uses delta: `Δtriangles = |neighbors(u) ∩ neighbors(v)|` on each edge add
- BFS blast-radius: `cg.impactSubgraph(rootIds, ['CONTAINS'], 3)` is sub-millisecond on
  1M+ node graphs (one read-lock, in-memory BFS, no GQL compiler)

Use this for dependency impact analysis: "if this source document changes, which downstream
aggregates are affected?"

### Rayon parallel node scan

Node scans over 512+ nodes automatically parallelize across CPU cores via Rayon. DQ checks
on large Record sets scale linearly with core count. No configuration needed.

### Stateful standing query registry

Each LIVE VIEW gets its own `PlanExecutionState` — join accumulators, distinct sets, window
buffers. The registry maintains topological evaluation order with cycle detection: you cannot
accidentally create a circular DQ dependency. The state is lazy-initialized on the first
mutation, not at registration.

### Query cardinality estimation

The query compiler collects `label_cardinalities` and property `NDV` (number of distinct
values). For large DQ scans, it reorders joins to filter on the most selective predicate first
(`selectivity = 1.0 / NDV`). This is automatic — no query hints needed.

### Window functions for trend DQ

`LAG`, `LEAD`, `SLIDING_AVG`, `EXPANDING_SUM`, `ROW_NUMBER`, `PERCENT_RANK` are all
available. Use for anomaly detection on time-series data:

```cypher
MATCH (r:Record)
RETURN r.category, LAG(r.price, 1) OVER (PARTITION BY r.category ORDER BY r.ingestedAt) AS prev_price
```

### Full-text search for fuzzy record matching

`CALL db.fulltext.search('label:Function AND name:login')` — tantivy-backed full-text index
for fuzzy dedup across records with similar text fields. Combine with entity resolution
algorithms in `wc-core/src/algorithms/entity_resolution.rs`.

---

## Using SQL tooling with ArcFlow (PostgreSQL wire protocol)

ArcFlow includes a PostgreSQL wire protocol server. This means any tool that speaks
PostgreSQL — psql, DBeaver, Tableau, DataGrip, any PostgreSQL client library — can connect
directly to ArcFlow:

```bash
# Start ArcFlow with PG wire enabled
arcflow --pgwire --port 5432 --data ./mydb
```

```bash
# Connect with standard psql
psql -h localhost -p 5432 -d arcflow
```

**Important:** The PG wire protocol is a transport layer, not a SQL parser. You write
WorldCypher (ArcFlow's GQL-aligned query language), not SQL SELECT:

```sql
-- This is what you type in psql or DBeaver:
MATCH (r:Record) WHERE r.price < 0.01 RETURN r.id, r.price

-- Not SQL — the PG wire protocol carries WorldCypher to the engine
```

**What this enables:**
- Connect Tableau, Metabase, or any BI tool to ArcFlow and run graph queries from a
  familiar SQL client interface
- Use psql for interactive exploration during development
- Wire DBeaver or DataGrip to browse the graph schema and run ad-hoc queries
- Pipe results to any tool that reads tabular PostgreSQL output

**What it does not do:**
- ArcFlow does not parse `SELECT ... FROM ... JOIN` SQL. It parses WorldCypher/GQL.
- PG wire is the adoption on-ramp: your existing tooling connects, but you learn
  graph queries. GQL (ISO/IEC 39075) is the destination.

For this data pipeline use case: run the pipeline via TypeScript for full CDC integration
(live views fire on every write), then inspect results from psql or DBeaver for ad-hoc
analysis without leaving your existing SQL workflow.

---

## Architecture notes

### Two write paths

| Path | API | CDC fires? | Use when |
|---|---|---|---|
| GQL compiler | `batchMutate()`, `mutate()` | Yes — live views update | DQ monitoring, lineage edges |
| Direct engine | `cg.ingest()` / `db.ingestDelta()` | No | Content-hash dedup, max throughput |

### Node ID consistency

GQL `MERGE`/`CREATE` assigns sequential numeric IDs. `ingestDelta()` maps string IDs via
FNV hash. If you need to connect ingestDelta-created nodes to GQL-created nodes with
edges, pick one write path for the nodes on both ends of the edge.

### Live view predicate support

Currently supported in Z-set planner: `=`, `>`, `<`, `IS NULL`.
Use direct queries for: `>=`, `<=`, `<>`, `IN` lists, `CASE WHEN`.
These operators are planned for the Z-set planner in a future wave.

---

## What ArcFlow replaces, and why

| Tool | Replaced by | Why it's better |
|---|---|---|
| **dbt** | `batchMutate()` + `SET` | No YAML, no compilation step, lineage is automatic |
| **Great Expectations** | `CREATE LIVE VIEW` | In-process, sub-ms, no Python runtime, no checkpoint runner |
| **Airflow** | Stage + PipelineRun nodes | DAG is queryable, versioned, co-located with data |
| **Amundsen / DataHub** | `SOURCED_FROM` edges | Lineage is first-class, not a separate catalog |
| **Looker drill** | GQL graph traversal | No LLM, no separate BI tool, one query |
| **Snapshot tables** | `AS OF seq N` | WAL is the timeline, no ETL to snapshot tables |
| **NATS / Kafka** | Z-set delta + LIVE VIEW | In-process incremental computation, no broker |

The deeper point: each of these tools exists because relational databases treat data, lineage,
orchestration, and quality as separate concerns. A graph database treats them as first-class
connected entities in the same store. The connections that used to require a service boundary
become graph edges.

---

## GQL — ISO/IEC 39075:2024 and what makes ArcFlow unique

### What GQL is

GQL (Graph Query Language) is the ISO/IEC international standard for property graph databases,
published April 2024. It plays the same role for graph databases that SQL played for relational
databases: a portable, vendor-neutral query language that every conformant engine must support.

Every major graph vendor has either shipped or announced conformance: Neo4j, Google Spanner
Graph, Ultipa, AWS Neptune, Microsoft Fabric Graph. For enterprise adoption, GQL conformance
is increasingly a procurement requirement — the same way SQL was in the 1980s.

ArcFlow's query language is **WorldCypher**: a superset of openCypher (the de-facto open
standard before ISO GQL) that is being aligned with ISO GQL as the primary target.

### The strategy: ADOPT / EXTEND / DEFER

Every GQL feature gets an explicit decision (PAT-0029):

| Decision | Meaning | Example |
|---|---|---|
| **ADOPT** | Align ArcFlow syntax to the GQL standard | Label expressions `n:A\|B` |
| **EXTEND** | Support both GQL and ArcFlow syntax | Evidence algebra (`REFINE EDGE`) |
| **DEFER** | Wait for GQL stability before implementing | `GRAPH_TABLE` (SQL/PGQ interop) |

This is not passive drift — it is deliberate engineering. The risk of every standard alignment
project is that vendors silently break their own extensions. ArcFlow runs an extension
regression suite at every phase boundary: no GQL feature ships if any ArcFlow extension
regresses.

### What ArcFlow already implements from GQL today

The compiler (WorldCypher) implements most of the GQL syntax surface already:

**Pattern matching (GQL-0003):**
```cypher
-- Label expression disjunction: match either Person or Organization
MATCH (n:Person|Organization) RETURN n.name

-- Label expression conjunction
MATCH (n:Person&Employee) RETURN n

-- Quantified path patterns (GQL-native, not openCypher)
MATCH (a)-[:KNOWS]->{2,5}(b) RETURN a, b   -- between 2 and 5 hops
MATCH (a)-[:FEEDS]->+(b) RETURN a, b        -- one or more
MATCH (a)-[:FEEDS]->*(b) RETURN a, b        -- zero or more

-- Path modes
MATCH TRAIL (a)-[:KNOWS]->*(b) RETURN a, b  -- no repeated edges
MATCH SIMPLE (a)-[:KNOWS]->*(b) RETURN a, b -- no repeated nodes

-- Undirected edges (GQL GH02)
MATCH (a)~[:KNOWS]~(b) RETURN a, b
```

**Clause aliases (GQL GQ10–GQ13):**
```cypher
-- FILTER is a GQL alias for WHERE
MATCH (r:Record) FILTER r.price < 0.01 RETURN r.id

-- FOR is a GQL alias for UNWIND
FOR item IN ['A', 'B', 'C'] RETURN item

-- LET is a GQL alias for WITH
LET total = count(*) RETURN total
```

**Conditional execution (GQL V2, already in compiler):**
```cypher
MATCH (r:Record)
RETURN * NEXT
WHEN r.category = 'A' THEN
  MATCH (r)-[:SOURCED_FROM]->(d) RETURN d.path
WHEN r.category = 'B' THEN
  MATCH (r)-[:CONTAINS]->(sub) RETURN sub.id
ELSE
  RETURN null AS result
END
```

**GQLSTATUS codes (Clause 24 mandatory):** Every `QueryResult` carries a 5-digit GQLSTATUS:
- `00000` — success with rows
- `02000` — success, no data (empty result)
- Error outcomes map to GQL standard error class/subclass codes

**Transaction control:**
```cypher
START TRANSACTION READ ONLY
MATCH (r:Record) RETURN count(*)
COMMIT
```

**Session parameters:**
```cypher
SESSION SET timeout = 5000
SESSION SET memory_limit = '2GB'
```

### The vendor choices ArcFlow declares explicitly (PAT-0032)

GQL intentionally leaves certain data model dimensions as vendor choices. ArcFlow declares
these explicitly rather than treating them as gaps:

| GQL leaves open | ArcFlow decides | Why |
|---|---|---|
| Label cardinality | **Single label per node/edge** | Simplicity, performance; label expressions give multi-label semantics via queries |
| Edge directionality | **Directed by default** | Undirected via `~` syntax (GQL GH02); explicit direction is safer for pipeline lineage |
| Graph type | **Open graph type (GG01)** | Schema-free; label/edge conventions documented, not enforced by schema |
| Primary key | **Planned: MERGE deterministic** | GQL V2 track; currently MERGE uses sequential IDs |

A vendor choice made deliberately is a strength, not a gap. Declaring these choices is what
makes a GQL conformance statement trustworthy.

### What is beyond standard GQL — ArcFlow's moat (88+ unique features)

Standard GQL defines the floor. ArcFlow's unique capabilities are the ceiling no competitor
reaches. These are expressed through GQL-compatible syntax (CALL procedures, statement
extensions) so standard queries remain portable:

#### 1. LIVE queries — incremental computation (no GQL equivalent)

```cypher
-- Standing query: re-evaluates only the delta on each mutation
CREATE LIVE VIEW dq_zero_price AS
  MATCH (r:Record) WHERE r.price < 0.01 RETURN r.id

-- Read the live result
MATCH (row) FROM VIEW dq_zero_price RETURN row

-- Incremental algorithm execution
LIVE CALL algo.pageRank({label: 'Document', rel: 'SIMILAR'})
```

This is backed by Z-set algebra: a mathematical proof that incremental evaluation is exactly
equivalent to full batch re-evaluation. It is not polling. It is not approximate. It is
provably correct (PAT-0021).

Neo4j has no LIVE prefix. Ultipa has no standing queries. Spanner has no incremental
computation. This is the deepest technical moat in the GQL landscape.

For data pipelines: DQ live views fire on every write — no checkpoint runner, no scheduler,
no re-scan. The engine evaluates only what changed.

#### 2. Relationship skills — declarative edge construction

```cypher
-- Define a skill: LLM or embedding-driven
CREATE SKILL EntityResolver
  FROM PROMPT 'Resolve co-located entities'
  ALLOWED ON [Person, Organization]
  TIER SYMBOLIC

-- Reactive: auto-fires on node creation
CREATE REACTIVE SKILL auto_resolve
  ON :Person WHEN CREATED RUN EntityResolver

-- Embedding-driven: auto-creates edges when cosine similarity > threshold
CREATE SKILL SemanticLinker
  FROM EMBEDDING arcflow.cosine(source.embedding, target.embedding)
  THRESHOLD 0.8
  ALLOWED ON [Document, Concept]
  TIER NEURAL
```

No graph database has declarative relationship constructors that fire reactively. Neo4j has
APOC triggers. Ultipa has algorithms. Neither has SKILL as a first-class primitive combining
prompt definition, type constraints, tier classification, and reactive execution.

For data pipelines: auto-link related records from different sources without writing ETL code.

#### 3. Evidence algebra — confidence as first-class quantity

```cypher
-- Algebraic update: retracts old confidence, inserts new, tracks provenance
MATCH ()-[r:SOURCED_FROM]->()
REFINE EDGE r SET confidence = 0.95, observation = 'confirmed_2026'

-- Path confidence: multiplies confidences along a chain (evidence chain rule)
MATCH path = (a)-[:SOURCED_FROM*1..3]->(d)
RETURN a.id, arcflow.path_confidence(path) AS chain_confidence
```

Standard GQL `SET` is a property update. ArcFlow `REFINE` is algebraic: retract the old
Z-set entry, insert the new one, track who refined it and when. No other graph database
treats confidence as an algebraic quantity with reversible semantics.

#### 4. Temporal decay policies — facts age naturally

```cypher
CREATE DECAY POLICY standard_fact_decay
  HALF_LIFE 90 DAYS
  FLOOR_CONFIDENCE 0.05

ALTER LABEL Fact SET DECAY POLICY standard_fact_decay

-- Check entity health across all its facts
CALL algo.entityFreshness(entity)
  YIELD entity_health, stale_fact_count, critical_facts_stale
```

Formula: `floor + (base_confidence - floor) × 2^(-Δt / half_life_days)` — natural-floor
exponential, idempotent under WAL replay. Based on CountTRuCoLa (arXiv:2509.09474) and
Knowledge Vault corroboration scaling (KDD 2014).

For data pipelines: data quality degrades over time. Model it as physics, not just flags.

#### 5. ASOF JOIN — time-series in a graph database

```cypher
MATCH (p:DailyBar) ASOF JOIN (f:Fundamental)
  ON p.symbol = f.symbol AND p.date >= f.avail_date
RETURN p.date, p.symbol, f.revenue
```

Temporal point-in-time joins are standard in time-series databases (DuckDB, kdb+) but absent
from every graph database. ArcFlow bridges the graph and time-series worlds in one query.

For data pipelines: correlate event logs to reference snapshots without pre-joining tables.

#### 6. Durable workflows as graph subgraphs

```cypher
CREATE WORKFLOW onboarding
-- Step nodes + NEXT edges = the DAG
-- Status/results stored as node properties
-- WAL-backed: recovery = WAL replay, no external state store
```

No separate orchestrator (Airflow, Temporal, Inngest). The graph IS the workflow state. Every
step is a node. Every transition is an edge. The pipeline DAG in section 0 of this example is
a minimal instance of this pattern.

#### 7. GPU-accelerated GraphBLAS + cuVS

- 25 CUDA kernels: SpMV semiring dispatch, SpGEMM, reduce/apply/eWise
- cuVS (RAPIDS): CAGRA/IVF-Flat/IVF-PQ GPU-native ANN search
- Apple Metal: PageRank, Louvain on Apple Silicon
- Auto-dispatch: Metal → CUDA → CPU with explicit backend reporting (ANTI-0003)

Ultipa claims "in-memory speed" but is CPU-only. Neo4j's vector index is CPU-only. ArcFlow
accelerates both graph algorithms and vector search on GPU.

### The flywheel that no competitor can express in GQL

```cypher
-- Step 1: new document arrives
CREATE (d:Document {content: '...'})

-- Step 2: reactive skill auto-embeds it (LIVE)
CREATE REACTIVE SKILL auto_embed
  ON :Document WHEN CREATED
  RUN SET node.embedding = arcflow.embed(node.content)

-- Step 3: live view auto-links similar documents (LIVE)
CREATE LIVE VIEW similar_docs AS
  MATCH (a:Document), (b:Document) WHERE a <> b
    AND arcflow.cosine(a.embedding, b.embedding) > 0.8
  MERGE (a)-[:SIMILAR {score: arcflow.cosine(a.embedding, b.embedding)}]->(b)
  RETURN a, b

-- Step 4: PageRank updates incrementally as new edges appear (LIVE)
CREATE LIVE VIEW doc_importance AS
  LIVE CALL algo.pageRank({label: 'Document', rel: 'SIMILAR'})
```

Insert a document. It auto-embeds. It auto-links to similar documents. PageRank updates
incrementally. All through declarative GQL-compatible syntax. Zero application code. Zero
external infrastructure. No other database — Neo4j, Ultipa, Spanner, or any SQL database —
can express this loop.

### Competitive landscape summary

| Capability | ArcFlow | Neo4j | Ultipa | Spanner |
|---|---|---|---|---|
| GQL conformance | Planned (I-INIT-0051) | ✓ | ✓ | ✓ |
| LIVE queries / incremental | ✓ | ✗ | ✗ | ✗ |
| Reactive skills | ✓ | ✗ | ✗ | ✗ |
| Evidence algebra | ✓ | ✗ | ✗ | ✗ |
| ASOF JOIN | ✓ | ✗ | ✗ | ✗ |
| Graph-native workflows | ✓ | ✗ | ✗ | ✗ |
| GPU vector search (cuVS) | ✓ | ✗ | ✗ | ✗ |
| GPU graph algorithms | ✓ (CUDA+Metal) | ✗ | ✗ | ✗ |
| Embed → skill → auto-link flywheel | ✓ | ✗ | ✗ | ✗ |
| Temporal decay policies | ✓ | ✗ | ✗ | ✗ |
| Live proofs (correctness verification) | ✓ | ✗ | ✗ | ✗ |

The standard is the floor. ArcFlow's extensions are the ceiling. Standard queries are fully
portable to any GQL-conformant engine. The extensions are what you stay for.
