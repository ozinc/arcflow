# Temporal + Spatial Parquet Ingestion

**What you'll build:** A queryable ArcFlow world model from a batch of Parquet
files containing per-frame entity tracking data (positions over time).

**Audience:** python, data-engineer

**Runtime:** ~5 minutes

**ArcFlow version:** 1.6.6

## Use case

Sports analytics, fleet tracking, robotics telemetry, sensor logs — anywhere
you have:

- A small set of **entities** (players, vehicles, sensors)
- A long timeline of **frames** with per-entity state (x, y, optionally z)
- Stored as **Parquet** in a DuckDB-friendly columnar shape
- And want **graph queries** over the temporal trajectories

This is the on-ramp for the world-model use case ArcFlow is positioned for.

## Run

```bash
uv sync
uv run python 00-make-sample.py            # synthesizes data/sample.parquet
uv run python 02-parquet-load.py
uv run python 04-temporal-queries.py
uv run python 05-validate-vs-duckdb.py
```

`01-schema-design.md` and `03-spatial-bulk-load.md` are reading-only steps
that walk through the design choices.

## What this recipe demonstrates

1. **Schema design** — entities as nodes, frames as scalar properties indexed
   per-entity. Why this shape over a "Frame node per timestamp" alternative.
2. **Parquet → ArcFlow batch ingest** — `pyarrow.parquet.read_table` →
   per-row `db.execute("CREATE ...")`. Throughput and memory profile.
3. **Spatial bulk-load** — registering positions for fast nearest-entity
   queries; how to do this without a per-frame index churn.
4. **Temporal queries in WorldCypher** — LAG-style per-entity windowing,
   trajectory length, per-frame nearest neighbor.
5. **Validation against DuckDB** — counts and aggregates match exactly across
   both engines on the same Parquet input. Cross-check in CI.

## Data

`data/sample.parquet` — synthesized at runtime by `00-make-sample.py`. Shape:
per-frame (x, y) for 22 players over 5 plays × 10 frames = 1100 rows —
the canonical multi-entity tracking layout. Synthesized, not real player
data. ≤ 50 KB in-tree after first run; the synthesizer is deterministic
so output is reproducible.

## Adapting to your own data

Swap `data/sample.parquet` for your file (or pass `--input` to step 02), then
adjust the schema fields in `01-schema-design.md` to match your columns. The
rest of the pipeline is shape-agnostic.

If your data is much larger (≥ 1M rows), batch the inserts (10K-row chunks)
and consider parallel ingestion. The recipe deliberately uses a small dataset
to keep CI fast.

## Notes

- Pinned to ArcFlow 1.6.6 (see `meta.toml.manifest_pin`).
- During alpha, `oz-arcflow` resolves through OZ's PEP 503 simple index at
  `https://staging.oz.com/pypi/simple/` — the same protocol PyPI uses, so
  `uv sync` treats `oz-arcflow` like any normal package. When the engine
  release manifest flips `python: planned` → `python: shipped`, the index
  pin becomes redundant and `pip install oz-arcflow` works against public
  PyPI as the canonical path.
