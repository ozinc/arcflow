# From Zero to Graph in 5 Minutes

## Install

```bash
curl -fsSL https://arcflow.dev/install | sh
```

Or if you already have it:
```bash
arcflow upgrade
```

Verify:
```bash
arcflow --version
arcflow gpu status    # shows CUDA/Metal acceleration if available
```

## 1. Interactive REPL — Your First Graph

```bash
arcflow --playground
```

This loads a demo social network. Try:

```cypher
-- See all people
MATCH (n:Person) RETURN n.name, n.age

-- Find connections
MATCH (a:Person)-[:KNOWS]->(b:Person) RETURN a.name, b.name

-- Run PageRank
CALL algo.pageRank()

-- Aggregate
MATCH (n:Person) RETURN n.city, count(*), avg(n.age)
```

## 2. Load Your Own Data — CSV Import

```bash
arcflow
```

In the REPL:
```
:import csv /path/to/your/data.csv MyLabel
```

All rows become graph nodes with label `MyLabel`. Properties are auto-detected from CSV headers (strings, integers, floats).

Then query:
```cypher
MATCH (n:MyLabel) RETURN count(*)
MATCH (n:MyLabel) RETURN n.column1, n.column2 ORDER BY n.column1 LIMIT 10
```

## 3. Real-World Example: Trading Pipeline

ArcFlow's sweet spot is **incremental computation on graph-structured data**. Here's the pattern from a validated quantitative finance pipeline (10/10 accuracy on 1.33M rows, 100% cell-by-cell match vs DuckDB):

### Load market data
```
:import csv prices.csv DailyBar
```

### Analytical queries
```cypher
-- Group by sector
MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)

-- Window functions: rolling statistics per symbol
MATCH (n:DailyBar)
RETURN n.symbol, n.date,
  lag(n.close, 1) OVER (PARTITION BY n.symbol ORDER BY n.date) AS prev_close,
  avg(n.close) OVER (PARTITION BY n.symbol ORDER BY n.date
    ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200,
  stddev_pop(n.close) OVER (PARTITION BY n.symbol ORDER BY n.date
    ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS vol_60d

-- Cross-sectional ranking
MATCH (n:DailyBar)
RETURN n.symbol, n.date,
  percent_rank() OVER (PARTITION BY n.date ORDER BY n.close) AS rank
```

### Live views — the incremental advantage
```cypher
-- Define once, maintained automatically on every mutation
CREATE LIVE VIEW sector_stats AS
  MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)

-- New data arrives → view updates incrementally (not full recompute)
CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-16', close: 195.0, sector: 'Tech'})

-- Read the pre-computed result (zero-cost)
MATCH (row) FROM VIEW sector_stats RETURN row
```

See [examples/trading-pipeline/](../../examples/trading-pipeline/) for the full example with all query patterns.

## 4. SDK — Embed in Your App

### TypeScript
```typescript
import { openInMemory } from '@arcflow/sdk'

const db = openInMemory()
db.mutate("CREATE (n:Person {name: 'Alice', age: 30})")
const result = db.query("MATCH (n:Person) RETURN n.name, n.age")
console.log(result.rows[0].get('name'))  // "Alice"
db.close()
```

### Python
```python
from arcflow import ArcFlow
db = ArcFlow()
db.execute("CREATE (n:Person {name: 'Alice', age: 30})")
result = db.execute("MATCH (n:Person) RETURN n.name, n.age")
```

### Rust
```rust
let store = wc_sdk::open_concurrent();
store.execute("CREATE (n:Person {name: 'Alice'})")?;
let result = store.execute("MATCH (n) RETURN n.name")?;
```

## 5. HTTP API — Connect From Anywhere

```bash
arcflow --http 8080
```

```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN count(*)"}'
```

## 6. MCP Server — For AI Agents

```bash
arcflow-mcp
```

Claude, Cursor, and other AI agents can query your graph directly via the Model Context Protocol.

## 7. Architecture — What ArcFlow Replaces

| Traditional Stack | ArcFlow Equivalent |
|---|---|
| Neo4j (graph DB) | Built-in graph store |
| Redis (cache) | In-memory, zero-copy |
| DuckDB (analytics) | Columnar scans, window functions |
| Kafka/NATS (streaming) | CDC + standing queries |
| Vector DB (embeddings) | HNSW vector index |
| Temporal (workflows) | Graph-native durable workflows |

All modules share one `GraphStore` in unified memory. No serialization. No network hops.

## Next Steps

- `CALL db.help` — full procedure reference in the REPL
- `CALL db.tutorial` — interactive 6-step walkthrough
- [Core Concepts](../core-concepts/graph-model.md) — graph model, WorldCypher, parameters
- [Tutorials](../tutorials/knowledge-graph.md) — build a knowledge graph
- [Recipes](../recipes/crud.md) — copy-paste patterns
- [API Reference](../reference/api.md) — TypeScript SDK API
- [Trading Pipeline Example](../../examples/trading-pipeline/) — full quantitative finance use case
