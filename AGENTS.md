# ArcFlow SDK

ArcFlow is a spatial-temporal graph database engine. WorldCypher is its query language (Cypher-compatible).
This repo contains the TypeScript SDK, documentation, examples, and compatibility reference.

## Quick start

```typescript
import { open, openInMemory } from '@arcflow/sdk'

const db = openInMemory()  // or open('./data') for persistence

// Write
db.mutate("CREATE (n:Person {name: 'Alice', age: 30})")

// Read (typed — age is number, not string)
const result = db.query("MATCH (n:Person) RETURN n.name, n.age")
result.rows[0].get('name')  // "Alice"
result.rows[0].get('age')   // 30

// Parameters (prevents injection)
db.query("MATCH (n:Person {name: $name}) RETURN n", { name: 'Alice' })

// Batch mutations (single write lock)
db.batchMutate([
  "MERGE (a:Person {id: 'p1', name: 'Alice'})",
  "MERGE (b:Org {id: 'o1', name: 'Acme'})",
])

// Algorithms (no projection setup)
db.query("CALL algo.pageRank()")
db.query("CALL algo.louvain()")

// Vector search
db.mutate("CREATE VECTOR INDEX idx FOR (n:Doc) ON (n.embedding) OPTIONS {dimensions: 1536, similarity: 'cosine'}")
db.query("CALL algo.vectorSearch('idx', $vec, 10)", { vec: JSON.stringify([0.1, 0.2]) })

// Full-text search (BM25)
db.mutate("CREATE FULLTEXT INDEX ft FOR (n:Person) ON (n.name)")
db.query("CALL db.index.fulltext.queryNodes('ft', 'Alice')")

// Error handling
import { ArcflowError } from '@arcflow/sdk'
try { db.query("INVALID") } catch (e) {
  if (e instanceof ArcflowError) console.log(e.code, e.category, e.suggestion)
}

db.close()
```

## API surface

```typescript
open(dataDir: string): ArcflowDB        // Persistent (WAL-journaled)
openInMemory(): ArcflowDB               // In-memory (for testing)

interface ArcflowDB {
  version(): string
  query(cypher: string, params?: QueryParams): QueryResult
  mutate(cypher: string, params?: QueryParams): MutationResult
  batchMutate(queries: string[]): number
  isHealthy(): boolean
  stats(): { nodes: number; relationships: number; indexes: number }
  close(): void
}

type QueryParams = Record<string, string | number | boolean | null>

interface QueryResult {
  columns: string[]
  rows: TypedRow[]
  rowCount: number
  computeMs: number
}

interface TypedRow {
  get(column: string): string | number | boolean | null   // supports 'n.name' and 'name'
  toObject(): Record<string, string | number | boolean | null>
}

interface MutationResult extends QueryResult {
  nodesCreated: number; nodesDeleted: number
  relationshipsCreated: number; relationshipsDeleted: number
  propertiesSet: number
}

class ArcflowError extends Error {
  code: string           // "EXPECTED_KEYWORD", "LOCK_POISONED", "DB_CLOSED"
  category: 'parse' | 'validation' | 'execution' | 'integration'
  suggestion?: string
}
```

## WorldCypher reference

### Write operations
```cypher
CREATE (n:Label {key: 'value', num: 42})
CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})
MERGE (n:Label {id: 'unique-key', name: 'value'})
MATCH (n:Person {name: 'Alice'}) SET n.age = 31
MATCH (n:Person {name: 'Alice'}) REMOVE n.email
MATCH (n:Person {name: 'Alice'}) DELETE n
MATCH (n:Person {name: 'Alice'}) DETACH DELETE n
```

### Read operations
```cypher
MATCH (n:Person) RETURN n.name, n.age
MATCH (n:Person) WHERE n.age > 25 RETURN n.name ORDER BY n.age DESC LIMIT 10
MATCH (n:Person) WHERE n.name CONTAINS 'ali' RETURN n
MATCH (n:Person) WHERE n.name STARTS WITH 'A' RETURN n
MATCH (a:Person)-[:KNOWS]->(b:Person) RETURN a.name, b.name
MATCH (a)-[:KNOWS*1..3]->(b) RETURN b.name
MATCH (a:Person {id: $pid}) MATCH (b:Org {id: $oid}) RETURN a.name, b.name
MATCH (n) WHERE (n:Person OR n:Company) RETURN n.name
MATCH (n:Person) RETURN count(*), avg(n.age), sum(n.score)
RETURN COALESCE(n.email, 'none')
RETURN toLower(n.name)
UNWIND [1, 2, 3] AS x RETURN x
MATCH (n:Person) WITH n WHERE n.age > 25 RETURN n.name
MATCH (n:Person) AS OF 1700000000 RETURN n.name
```

### Window functions
```cypher
MATCH (n:DailyBar) RETURN n.symbol, n.date,
  lag(n.close, 1) OVER (PARTITION BY n.symbol ORDER BY n.date) AS prev_close
MATCH (n:DailyBar) RETURN n.symbol, n.date,
  lead(n.close, 21) OVER (PARTITION BY n.symbol ORDER BY n.date) AS future_close
MATCH (n:DailyBar) RETURN n.symbol, n.date,
  avg(n.close) OVER (PARTITION BY n.symbol ORDER BY n.date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200
MATCH (n:DailyBar) RETURN n.symbol, n.date,
  stddev_pop(n.close) OVER (PARTITION BY n.symbol ORDER BY n.date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS vol_60d
MATCH (n:DailyBar) RETURN n.symbol,
  percent_rank() OVER (PARTITION BY n.date ORDER BY n.close) AS rank
MATCH (n:DailyBar) RETURN n.symbol,
  row_number() OVER (PARTITION BY n.date ORDER BY n.close DESC) AS rn
```

### Live views (incremental computation)
```cypher
CREATE LIVE VIEW sector_stats AS MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)
MATCH (row) FROM VIEW sector_stats RETURN row
CALL db.liveViews
```

### Indexes
```cypher
CREATE VECTOR INDEX name FOR (n:Label) ON (n.prop) OPTIONS {dimensions: N, similarity: 'cosine'}
CREATE FULLTEXT INDEX name FOR (n:Label) ON (n.prop)
```

### Algorithms (CALL algo.*)
pageRank, confidencePageRank, betweenness, closeness, degreeCentrality,
louvain, leiden, communityDetection, connectedComponents,
clusteringCoefficient, nodeSimilarity, triangleCount, kCore, density, diameter,
allPairsShortestPath, nearestNodes, confidencePath,
vectorSearch(index, vector, k), similarNodes, hybridSearch,
graphRAG, graphRAGContext, graphRAGTrusted,
compoundingScore, contradictions, audienceProjection(weights), factsByRegime,
multiModalFusion

### Database operations (CALL db.*)
stats, schema, labels, types, propertyKeys, indexes, nodeCount, relationshipCount,
version, capabilities, doctor, fingerprint, validateQuery(cypher),
export, import, import.csv, clear, demo,
help, procedures, tutorial,
index.fulltext.queryNodes(index, query),
checkpoint, changesSince, temporalCompare, temporalReplay,
views, liveViews, liveQueries, liveAlgorithms, reactiveSkills,
topics, provenance, replicationStatus

### Temporal (CALL temporal.*)
decay(halfLife, floor), trajectory, velocity(days)

### Reactive queries
```cypher
LIVE MATCH (n:Person) WHERE n.score > 0.9 RETURN n
LIVE CALL algo.pageRank()
CREATE LIVE VIEW name AS MATCH (n:Person) WHERE n.score > 0.9 RETURN n.name
```

### Session
```cypher
USE PARTITION 'workspace-id'
SET SESSION ACTOR 'user-id' ROLE 'admin'
```

## Caveats

- SET multiple properties: use separate SET clauses, not comma-separated
- UNWIND: literal lists only (no variable unwinding)
- MERGE relationship: may create duplicates if not careful with match criteria
- Parameters are string-coerced internally
- Metal GPU: set ARCFLOW_METAL_FORCE_UNAVAILABLE=true if module load hangs

## Repo structure

```
typescript/src/          # SDK source (index.ts, types.ts, errors.ts)
typescript/tests/        # SDK tests (Vitest)
docs/getting-started/    # Installation, quickstart, project setup
docs/core-concepts/      # Graph model, WorldCypher, parameters, results, persistence, errors
docs/tutorials/          # Knowledge graph, entity linking, vector search, algorithms
docs/recipes/            # CRUD, multi-match, merge, fulltext, temporal, batch, GraphRAG
docs/reference/          # API, compatibility matrix, known issues, worldcypher.yaml
docs/use-cases/          # Knowledge management, RAG, sports analytics, behavior graphs
examples/                # Runnable example projects
```

## For agents modifying this SDK

1. Source is in `typescript/src/`
2. Tests are in `typescript/tests/`
3. Run: `just test` (or `cd typescript && npm test`)
4. Build: `just build` (or `cd typescript && npm run build`)
5. Lint: `just lint` (Biome)
6. The SDK wraps `@arcflow/core` (the raw napi-rs binding)

## Extended reference

See `llms-full.txt` for the complete WorldCypher syntax with every pattern and procedure.
