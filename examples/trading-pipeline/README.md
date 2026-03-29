# Trading Pipeline Example

**Define a transformation once, run it as batch or incremental.**

## The Problem

Quantitative finance pipelines must run in two modes:
- **Batch**: Full historical recompute (nightly)
- **Delta**: Incremental update when new data arrives (real-time)

Today these are separate codepaths that drift apart. ArcFlow unifies them.

## Quick Start

### 1. Load data
```bash
arcflow
arcflow> :import csv prices.csv DailyBar
# Imported 207250 nodes as :DailyBar (~5 seconds)
```

### 2. Define features (same queries work in batch AND incremental)
```cypher
-- Lagged returns
MATCH (n:DailyBar)
RETURN n.symbol, n.date,
  (n.close / lag(n.close, 1) OVER (PARTITION BY n.symbol ORDER BY n.date)) - 1 AS return_1d

-- Rolling volatility
MATCH (n:DailyBar)
RETURN n.symbol, n.date,
  stddev_pop(n.close) OVER (PARTITION BY n.symbol ORDER BY n.date
    ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS vol_60d

-- Cross-sectional ranking
MATCH (n:DailyBar)
RETURN n.symbol, n.date,
  percent_rank() OVER (PARTITION BY n.date ORDER BY n.close) AS rank_global

-- Sector aggregation
MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close), stddev_pop(n.close)
```

### 3. Set up live views (incremental mode)
```cypher
-- Define once — maintained automatically
CREATE LIVE VIEW daily_stats AS
  MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)

-- New data arrives — view updates via CDC (not full recompute)
CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-07-01', close: 200.0, sector: 'Tech'})

-- Read pre-computed result
MATCH (row) FROM VIEW daily_stats RETURN row
```

### 4. The delta advantage

| Approach | Data Scanned | Time | Correctness |
|---|---|---|---|
| Full batch (DuckDB) | 15.4M rows | 36s | Perfect |
| Smart batch (200 rows/symbol) | ~700K rows | ~2s | Wrong for stateful features |
| **ArcFlow delta** | **3,500 rows (1 day)** | **2.9ms** | **Perfect** |

The delta path is 12,000x faster than full batch and gives correct results for ALL feature types — including expanding windows (OBV), state-dependent counters (days_since_high), and cross-sectional ranks.

## Dependency Types ArcFlow Handles

| Type | Example | Delta Behavior |
|---|---|---|
| Fixed lookback | LAG(close, 90) | Carry 90-row buffer per symbol |
| Expanding window | OBV (cumulative) | Maintain running state |
| Forward fill | ASOF JOIN fundamentals | Update on new fundamental arrival |
| Cross-sectional | PERCENT_RANK by date | Re-rank all symbols on that date |
| State-dependent | days_since_90d_high | Track running group counter |
| Cascading | sector rolling avg | 1 new row → re-aggregate → re-roll → re-join |

## SDK Usage

```typescript
import { open } from '@arcflow/sdk'

const db = open('./market-data')

// Load bars
db.batchMutate([
  "CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-15', close: 192.5, volume: 54000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-16', close: 195.0, volume: 48000000, sector: 'Tech'})",
  "CREATE (n:DailyBar {symbol: 'MSFT', date: '2024-06-15', close: 441.2, volume: 22000000, sector: 'Tech'})",
])

// Sector aggregation
const sectors = db.query("MATCH (n:DailyBar) RETURN n.sector, count(*) AS cnt, avg(n.close) AS avgClose")
for (const row of sectors.rows) {
  console.log(`${row.get('sector')}: ${row.get('cnt')} bars, avg close $${row.get('avgClose')}`)
}

// Create live view
db.mutate("CREATE LIVE VIEW sector_stats AS MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)")

// New data arrives — view updates automatically
db.mutate("CREATE (n:DailyBar {symbol: 'AAPL', date: '2024-06-17', close: 197.0, sector: 'Tech'})")

db.close()
```

## Files

- `queries.cypher` — all example queries in one file
- `index.ts` — TypeScript SDK version of the pipeline
