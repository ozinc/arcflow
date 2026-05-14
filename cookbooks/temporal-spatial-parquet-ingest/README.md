# Temporal + Spatial Parquet Ingestion

> **Parquet batches of per-frame entity tracking → a queryable
> ArcFlow world model, validated cell-for-cell against DuckDB on the
> same input.**

**Audience:** python · data-engineer · ml
**Runtime:** ~5 minutes
**Pins:** `oz-arcflow==0.7.1`

The on-ramp for batch-Parquet-to-graph migrations — sports analytics,
fleet tracking, robotics telemetry, sensor logs. A small set of
entities, a long timeline of per-entity state, columnar storage,
graph-shaped queries you'd rather not write as recursive SQL.

## The four hard problems this addresses

Parquet-to-graph ingestion looks deceptively simple. Four engineering
walls every team hits the moment the dataset grows past a few million
rows:

1. **Columnar source vs row-shaped naive ingest.** Parquet is columnar
   — values for the same column live together. Naive per-row
   `db.execute("CREATE …")` re-traverses the parser per row at
   ~3–10K writes/sec and decays under graph growth. A 10 M-row dataset
   takes hours. The bulk-array path (`bulk_create_nodes` /
   `bulk_create_relationships`) bypasses the parser and writes at
   ~1M ops/sec — the difference between minutes and hours.

2. **Per-frame spatial index churn.** Spatial indexes (R*-tree) benefit
   from values being loaded together rather than interleaved. Naive
   ingest of `entity-1 frame 0, entity-2 frame 0, entity-1 frame 1, …`
   triggers index re-balance per row. The graph shape attaches
   positions to per-observation edges and inserts the spatial index in
   bulk after ingest — one re-balance instead of millions.

3. **Cross-engine validation against the source of truth.** How do
   you *trust* that the graph contains the same data as the Parquet
   file that fed it? Counts can be off by one if a NULL slips through;
   aggregates can drift if a type coercion silently rounds. The recipe
   runs the same aggregate questions against both ArcFlow and DuckDB
   on the same Parquet input and asserts cell-for-cell agreement —
   the CI gate every ingest pipeline should have.

4. **Schema rigidity when the Parquet schema evolves.** Adding a new
   column to the source Parquet means application changes across the
   ingest, the storage layer, every query that touches the column,
   and the downstream consumers. In the graph: new column → new
   property on the relevant node or edge → existing queries keep
   working unchanged; new queries reach the new property by name.

## What you'll build

1. **`00-make-sample.py`** — synthesizes `data/sample.parquet`: 22
   entities × 5 plays × 10 frames per play = 1100 per-frame (x, y)
   rows in the canonical multi-entity tracking layout.
2. **`02-parquet-load.py`** — Parquet → ArcFlow ingest. Discusses
   throughput and the bulk vs per-row trade-off.
3. **`04-temporal-queries.py`** — LAG-style per-entity windowing,
   trajectory length, per-frame nearest-entity questions.
4. **`05-validate-vs-duckdb.py`** — same counts and aggregates run
   against both engines on the same Parquet input; the cookbook fails
   loudly if they disagree.
5. **`01-schema-design.md` + `03-spatial-bulk-load.md`** —
   reading-only design rationale (entities-as-nodes-and-positions-as-
   edges; bulk-spatial-load pattern).

## Run

```bash
uv sync
uv run python 00-make-sample.py     # synthesizes data/sample.parquet
uv run python 02-parquet-load.py
uv run python 04-temporal-queries.py
uv run python 05-validate-vs-duckdb.py
```

`data/sample.parquet` ≤ 50 KB after the first run; the synthesizer is
deterministic so output is reproducible. Swap it for your own Parquet
to test against real data — the schema mapping in `_load.py` is the
single point of customisation.

## Capabilities exercised

| Capability | What it does for Parquet ingestion |
|---|---|
| `bulk_create_nodes` / `bulk_create_relationships` | ~1 M ops/sec bulk path; bypasses the Cypher parser for batch ingest |
| Spatial index over edge properties | One bulk re-balance after ingest, not per-row churn |
| Window functions in WorldCypher (`lag`, `lead`, `OVER (PARTITION BY entity ORDER BY frame)`) | Per-entity trajectory queries without leaving the engine |
| DuckDB cross-validation as CI gate | Cell-for-cell equivalence against the source of truth catches silent drift |
| `result.to_arrow()` for read-back | Zero-copy typed Arrow buffers for pandas/polars/duckdb hand-off |

## Rust SDK alongside

The `rust/` subfolder ships the same ingest + validate recipe via the
Rust SDK + the `parquet` / `arrow` Rust crates — one process reads the
columnar source, lands rows into ArcFlow's bulk-create path, and runs
the validate query loop against both engines. Useful when the ingest
pipeline itself is a Rust service rather than a one-shot Python job.

## See also

- [`from-sql-to-arcflow`](../from-sql-to-arcflow/) — the broader SQL→graph migration story (DuckDB queries side-by-side with WorldCypher)
- [`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/) — the substrate flagship; multi-stream tracking at 60 Hz where this recipe's pattern scales to
- [`fraud-graph-traversal`](../fraud-graph-traversal/) — another Parquet-fed pattern, focused on AML traversal queries
