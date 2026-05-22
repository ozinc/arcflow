# Rust SDK · From SQL to ArcFlow

The same three side-by-side comparisons as the Python version (`../`),
routed through the shipped Rust SDK + the `duckdb` Rust crate. One Rust
process holds both connections — DuckDB for the tabular workload,
ArcFlow's `ConcurrentStore` for the graph-shaped questions — and runs
both side of each comparison without leaving the process.

## When the Rust version pays off

- **Hybrid workloads in one process.** Trading platform, fraud
  pipeline, recommendation engine — many production stacks have both
  tabular OLTP queries and graph-shaped questions. One Rust binary
  holding both engines means no network hop between them, no
  serialization, no consistency reconciliation.
- **The same `_confidence` column reaches `algo.confidencePageRank` in
  ArcFlow.** Once the comparison has shown the SQL side how confidence
  becomes a filter, the Rust process can demonstrate
  `algo.confidencePageRank` on the ArcFlow side without rewiring —
  Python users would re-execute via `db.execute()`; Rust users can
  also subscribe to live updates as the underlying employment graph
  mutates.
- **PostgreSQL wire access alongside.** The same Rust process can
  expose its ArcFlow instance over the PG wire so external SQL clients
  attach without code changes. Mixed-tooling teams keep their
  existing SQL muscle memory for SQL-shaped queries.

## Run

```bash
cargo run --release --bin 01-shared-coworkers
cargo run --release --bin 02-confidence-tiered-query
cargo run --release --bin 03-multi-hop-industry
```

## Cargo layout

```
rust/
├── Cargo.toml                          # arcflow-sdk, duckdb (bundled)
├── src/
│   ├── lib.rs                          # fixture loaded into BOTH engines
│   └── bin/
│       ├── 01-shared-coworkers.rs      # one-edge walk vs 4 self-joins
│       ├── 02-confidence-tiered-query.rs # flat filter, same shape
│       └── 03-multi-hop-industry.rs    # one MATCH chain vs 5 CTEs
```
