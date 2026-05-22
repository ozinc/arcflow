# Lakehouse Count Fast-Path

> **`MATCH (f:Frame) RETURN count(f)` against a 311-million-row Parquet
> dataset, sub-second wall time, zero column reads. Every byte stays
> on disk; the answer comes from per-row-group `num_rows` summed
> across the parquet footer.**

**Audience:** python · data-engineer · ml
**Runtime:** ~3 minutes (synthesised sample); the real-world dataset
this pattern was first proven on is 311M frames (NFL 2025 tracking
data).
**Pins:** `oz-arcflow==0.8.0`

The cookbook for one of the load-bearing ArcFlow promises: counting
high-cardinality immutable rows in a Lakehouse partition without
touching column data, paying memory for the rows, or moving bytes off
disk.

## What this shows

ArcFlow's Smart Reader (inside the [World Store](/docs/concepts/layers/world-store)) reads the parquet footer
to plan the cheapest possible scan for the query at hand. For a pure
`count(*)`, that cheapest scan is **zero range fetches** — the engine
sums the per-row-group `num_rows` from the footer and returns. No
column chunk bytes leave object storage. No engine RAM grows with
dataset size. The cost is footer-parse time per file: ~tens of
microseconds.

The proof point: the same path returned `311,433,983` against a
real NFL Next Gen Stats partition (Merlin Phase B acceptance, May
2026). Sub-second wall time on a laptop, against a partition that
would have been unworkable through any row-materialising read path.

## What you need

A Hive-partitioned Parquet tree. The canonical shape:

```text
<root>/<table>/<part-key>=<value>/<part-key>=<value>/<file>.parquet
```

The recipe synthesises a small one (`./data/lake/`) so you can run it
without external data. Once the pattern clicks, point the same code at
a real lakehouse.

## Run it

```bash
# Synthesise a tiny Hive-partitioned tree (~10k rows across 3 partitions)
python 00-make-sample.py

# Register the virtual label + run the count
python 01-count.py
# {'n': 10000}  ← read from parquet footers, no column scan
```

## The worked example

```python
# 01-count.py
import arcflow
import os

os.environ["OZ_LAKE_ROOT"] = "./data/lake"

db = arcflow.ArcFlow("./workspace")

# Register a virtual label backed by the parquet partition glob.
# Rows live in the Lakehouse; the engine holds schema + catalog pointer.
db.register_virtual_partition(
    label="Frame",
    partition="lake://nfl/tracks/{season}/{week}",
)

# Count(*) against the virtual label.
# Plan: zero range fetches. Result: sum of num_rows across footers.
result = db.execute("MATCH (f:Frame) RETURN count(f) AS n")
print(result)
# {'n': 10000}
```

The same query against a real 311M-row partition returns the same
shape — only the value of `n` changes. The wall time stays bounded by
footer-parse cost, not row count.

## Why this is its own cookbook

The companion recipe
[`virtual-labels-over-parquet`](../virtual-labels-over-parquet/)
covers the general shape — declaring virtual labels, the layer
doctrine, the catalog story. This recipe zooms in on **the count
case** because:

1. It is the **first Smart Reader path shipped** (commit `b3f7958d`,
   v0.8.1). Other plan shapes — column-projection scans, predicate
   pushdown, the GPU-direct transport — are part of the same design
   and ship as the engine's read fabric expands.
2. The count case is what most ingest pipelines reach for first.
   "Did all the rows land? How many are in this partition?" — those
   answers should be sub-second and free, not a full table scan.
3. It is the cleanest demonstration of the layer doctrine. The
   [World Graph](/docs/concepts/layers/world-graph) holds identity
   (the `Frame` label, the typed catalog entry, the schema). The
   [World Store](/docs/concepts/layers/world-store) holds the bytes.
   The Cypher pattern crosses the boundary; the engine plans the
   smallest possible byte fetch; the answer is correct without
   materialising a single row.

## What's *not* in this cookbook (yet)

These ship as the engine's read fabric expands; the page describes
target end-state where helpful:

- **Column-projection scans.** `MATCH (f:Frame) WHERE f.season = 2024
  RETURN f.x, f.y` — pulls only the `x` and `y` column chunks for
  matching row groups. Stats-based row-group skip prunes the rest.
- **Predicate pushdown across row groups.** Min/max statistics on
  indexed columns let the planner skip row groups before any data
  reads.
- **GPU-direct transport.** When the projection routes to a GPU
  consumer (model inference, vector index probe), the engine reads
  bytes directly from NVMe into device memory via `cuFileRead`.
- **Arrow-IPC sidecar transport.** When the read consumer is an
  inference sidecar (separate crash domain), the transport delivers
  results via shared-memory Arrow IPC over UDS.

See [`docs/concepts/layers/world-store-serve.mdx`](/docs/concepts/layers/world-store-serve)
for the full Smart Reader design.

## Try it on your own data

Replace the synthesised tree with a real one:

```python
os.environ["OZ_LAKE_ROOT"] = "/path/to/your/lake/root"

db.register_virtual_partition(
    label="YourLabel",
    partition="lake://your/table/{partition_var_1}/{partition_var_2}",
)

result = db.execute("MATCH (n:YourLabel) RETURN count(n) AS n")
```

Iceberg manifests work too — the substrate's catalog reader is
Iceberg-shaped (Polaris, Unity, AWS Glue, or a plain manifest on
local disk). For Iceberg-backed partitions, point the resolver at
the manifest and use the standard `lake://` form.

## See also

- [Virtual Labels Over Parquet](../virtual-labels-over-parquet/) —
  the general-purpose companion recipe.
- [World Store](/docs/concepts/layers/world-store) — the substrate
  the Smart Reader sits inside.
- [Smart Reader](/docs/concepts/layers/world-store-serve) — the
  format-aware read planner + lane-explicit transport design.
- [Architecture](/docs/architecture) — the in-process engine that
  makes all of the above one Cypher pattern away.
