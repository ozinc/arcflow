// ArcFlow Trading Pipeline — Example Queries
// Load data first: :import csv prices.csv DailyBar

// ── Basic Analytics ──────────────────────────────────────────

// Count all rows
MATCH (n:DailyBar) RETURN count(*)

// Group by sector
MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)

// Order by date
MATCH (n:DailyBar) WHERE n.symbol = 'AAPL' RETURN n.date, n.close ORDER BY n.date LIMIT 20

// Point query
MATCH (n:DailyBar) WHERE n.symbol = 'AAPL' AND n.date = '2024-06-15' RETURN n.close, n.high, n.volume

// ── Window Functions (per-symbol time series) ────────────────

// LAG: previous day's close
MATCH (n:DailyBar) RETURN n.symbol, n.date, lag(n.close, 1) OVER (PARTITION BY n.symbol ORDER BY n.date) AS prev_close

// LEAD: future close (21 days ahead)
MATCH (n:DailyBar) RETURN n.symbol, n.date, lead(n.close, 21) OVER (PARTITION BY n.symbol ORDER BY n.date) AS future_close

// Rolling average (SMA-200)
MATCH (n:DailyBar) RETURN n.symbol, n.date, avg(n.close) OVER (PARTITION BY n.symbol ORDER BY n.date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200

// Rolling volatility (60-day standard deviation)
MATCH (n:DailyBar) RETURN n.symbol, n.date, stddev_pop(n.close) OVER (PARTITION BY n.symbol ORDER BY n.date ROWS BETWEEN 59 PRECEDING AND CURRENT ROW) AS vol_60d

// ROW_NUMBER for top-N per group
MATCH (n:DailyBar) RETURN n.symbol, n.date, n.close, row_number() OVER (PARTITION BY n.date, n.sector ORDER BY n.close DESC) AS sector_rank

// ── Cross-Sectional Rankings ─────────────────────────────────

// Percentile rank across all symbols on each date
MATCH (n:DailyBar) RETURN n.symbol, n.date, percent_rank() OVER (PARTITION BY n.date ORDER BY n.close) AS rank_global

// Rank within sector
MATCH (n:DailyBar) RETURN n.symbol, n.date, n.sector, percent_rank() OVER (PARTITION BY n.date, n.sector ORDER BY n.close) AS rank_in_sector

// ── Live Views (Incremental Computation) ─────────────────────

// Define a live view — maintained automatically via CDC
CREATE LIVE VIEW sector_stats AS MATCH (n:DailyBar) RETURN n.sector, count(*), avg(n.close)

// Read pre-computed results (zero cost)
MATCH (row) FROM VIEW sector_stats RETURN row

// Insert new data — live view updates incrementally
CREATE (n:DailyBar {symbol: 'NEW', date: '2024-07-01', close: 100.0, sector: 'Tech'})

// Check live view status
CALL db.liveViews

// ── Graph Algorithms ─────────────────────────────────────────

// PageRank (after relationships are created)
CALL algo.pageRank()

// Connected components
CALL algo.connectedComponents()

// Community detection
CALL algo.louvain()

// ── Skills (Relationship Inference) ──────────────────────────

// Create a skill that links similar entities
CREATE SKILL sector_linker FROM PROMPT 'Link companies in same sector' ALLOWED ON [DailyBar] TIER SYMBOLIC

// Execute skill on existing nodes
PROCESS NODE (n:DailyBar)

// Make it reactive — auto-execute on new data
CREATE REACTIVE SKILL auto_link ON :DailyBar WHEN CREATED RUN sector_linker

// ── Diagnostics ──────────────────────────────────────────────

CALL db.version
CALL db.stats
CALL db.liveSkills
CALL db.liveViews
