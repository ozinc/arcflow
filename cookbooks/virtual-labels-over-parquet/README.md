# Virtual Labels Over Parquet — Lakehouse Fast-Path

> **A Hive-partitioned Parquet tree, mounted as a queryable graph
> label, with the row data staying zero-copy in the source partitions.**

**Audience:** python · data-engineer · ml
**Runtime:** ~5 minutes
**Pins:** `oz-arcflow==0.8.0`

The cookbook for consumers ingesting **high-cardinality immutable
rows** — observation streams, telemetry samples, per-frame tracking,
event-stream rows. The path that opens when the dataset crosses the
point at which `bulk_create_*` into an Owned label stops being the
right answer.

## Why virtual labels

The pre-`0.8.0` ingest path expanded every row through the engine's
property-bag representation. For a low-cardinality mutable class —
twenty players, a hundred plays, a few thousand chartings — that's
fine and remains the right answer. For a high-cardinality immutable
class — a million frames, a billion sensor samples, a season of
telemetry — it forced a memory profile that grew with the source.

The substrate rewrite that landed in `0.8.0` separates the two
concerns. The **World Graph** owns identity, topology, and mutable
low-cardinality state. The **Perception Lake** owns immutable
observation rows — every byte stays in the source Parquet partitions.
The graph holds the typed schema, the adjacency, and a catalog
pointer; the row data stays where it was, accessed via columnar scan.

A *virtual label* is the syntactic anchor for that separation. You
declare it once; from then on, your Cypher queries treat the
Lakehouse rows as graph nodes — same `MATCH` patterns, same property
access — without ever materialising them into engine RAM.

## What you need

A Hive-partitioned Parquet tree. The canonical shape:

```text
<root>/<table>/<part-key>=<value>/<part-key>=<value>/<file>.parquet
```

Concrete examples:

- `lake://nfl/tracks/season=2025/week=07/game_key=59937.parquet`
- `lake://sensors/temperature/year=2026/month=03/day=14/sensor.parquet`
- `lake://logs/access/date=2026-05-15/hour=12/host-001.parquet`

Anything that opens as an Iceberg manifest works. The substrate's
catalog reader is Iceberg-shaped — Polaris, Unity, AWS Glue catalog,
or a plain manifest file on local disk are all readable.

## The `lake://` URI scheme

Virtual labels are registered against a *partition pattern*:

```text
lake://<mount>/<table>/{var}=<glob>[/{var}=<glob>]…/<file-glob>.parquet
```

| Element | Meaning |
|---|---|
| `lake://` | The Lakehouse URI scheme. Resolves through the workspace's catalog mount config. |
| `<mount>` | A named mount point — typically the dataset's logical name. Configured at workspace open time. |
| `<table>` | The table directory under the mount. |
| `{var}=<glob>` | A Hive-partitioned column. The brace-delimited variable name binds at registration; the glob narrows the partitions in scope. |
| `<file-glob>.parquet` | The file shape. Often `*.parquet` to match every file in a partition. |

Template variables matter. The registration `lake://nfl/tracks/{season}/{week}` admits any `season=*` / `week=*` partition under `tracks/` and gives the engine variables it can use for partition pruning at query time.

## Register a virtual label

Two ways: DDL through Cypher, or the direct Python FFI.

### Via DDL

```cypher
CREATE NODE LABEL Frame (
  entity_id STRING,
  ts        TIMESTAMP,
  x         DOUBLE,
  y         DOUBLE,
  speed     DOUBLE
) VIRTUAL FROM PARTITION 'lake://nfl/tracks/{season}/{week}';
```

The DDL is parsed, the typed schema is checked against the partition's
Parquet schema, and a `VirtualLabelEntry { label, partition_pattern,
schema_ref, resolver_kind }` row is committed to the catalog manifest
at `<workspace>/canonical/manifest_<epoch>.json`. The manifest commit
is atomic — `write-tmp + fsync + atomic_rename` with two-file protocol
(`F_FULLFSYNC` on macOS, `fdatasync` + drive-cache flush on Linux).
Survives `SIGKILL` mid-write; epochs are monotonic.

### Via Python FFI

For ingest pipelines that prefer to skip the Cypher round-trip:

```python
from arcflow import ArcFlow

db = ArcFlow("/path/to/workspace")
epoch = db.register_virtual_partition(
    label="Frame",
    partition="lake://nfl/tracks/{season}/{week}",
)
print(f"registered at epoch {epoch}")
# → registered at epoch 7
```

The C ABI counterpart is
`arcflow_register_virtual_partition(session, label, partition) -> i64`.

Run `00-make-sample.py` to synthesize a small Hive-partitioned Parquet
tree under `data/lake/`; run `01-register.py` to mount it as a virtual
label and inspect the catalog manifest.

## Query against virtual labels

The intent at the query surface is that virtual labels are
indistinguishable from Owned labels:

```cypher
-- The query you'd write
MATCH (f:Frame {entity_id: 'Unit-01'})
WHERE f.ts >= datetime('2026-03-14T08:00:00')
  AND f.ts <  datetime('2026-03-14T09:00:00')
RETURN f.ts, f.x, f.y, f.speed
ORDER BY f.ts
```

The planner-side rewriter for `MATCH (:VirtualLabel ...)` patterns —
which decomposes the pattern into a manifest scan + Parquet
predicate-pushdown — is the next wave of the substrate work. Until it
lands, queries against virtual labels return a typed
`QueryError::VirtualLabelNotYetQueryable`. The registration path is
real bytes on disk now; the read path is wired but gated.

What ships now: registration, schema validation against the Parquet
files, catalog manifest persistence, snapshot-pinned manifest reads,
the `oz://` URI vocabulary for the addressable resources.

## What stays Owned vs Virtual

The mechanical decision rule (per the
[World Graph](/docs/concepts/layers/world-graph) layer's R1–R3
boundary):

| Property | Owned | Virtual |
|---|---|---|
| Mutability | Mutable | Immutable |
| Cardinality | Low (≤ ~50K rows) | High |
| Read pattern | Property + traversal | Columnar predicate scan |
| Lives in | Engine stripe store | Lakehouse partitions |
| Storage path | `bulk_create_*` / Cypher `CREATE` | Hive-partitioned Parquet |

A few examples from a sports-tracking workload:

| Class | Cardinality | Mutability | Classification |
|---|---|---|---|
| `Player` | ~95 / season | mutable (roster, injury status) | Owned |
| `Play` | ~176 / game | mutable (charting corrections) | Owned |
| `Charting` | per source | mutable | Owned |
| `Frame` | ~1M / game | immutable | **Virtual** |
| `Telemetry` | ~1M / game | immutable | **Virtual** |

Edges are always Owned (R3). A `(:Frame)-[:TRACKED]->(:Player)` edge
has two Lake-resident endpoints but one Graph-resident edge — the
graph holds the adjacency, the Lake holds the row data, both layers
agree on the IDs.

## What you give up

- **No in-place mutation of virtual-label rows.** They're immutable by
  contract. Corrections happen via overlay tables in the Graph (an
  Owned class that the Query Engine joins at read time), not via
  in-place edits to the source Parquet. This is the design point —
  the alternative breaks every downstream Lakehouse consumer.
- **No write transactions that span Lake-side ingest.** New rows
  arrive in the Lake as new partitions; the manifest version
  advances; the graph picks up the new partition on its next manifest
  read. Reader-side snapshot isolation is via the manifest epoch.
- **Random-row property access is a Parquet scan.** Fast, but not
  microsecond-fast. If you need single-row random reads on a
  high-cardinality class, classify it as Owned — but you'll pay the
  bulk-ingest memory profile in return.

## Run

```bash
uv sync
uv run python 00-make-sample.py     # synthesizes data/lake/<table>/<part-key>=<value>/*.parquet
uv run python 01-register.py        # registers the virtual label + inspects the manifest
```

`data/lake/` ≤ 50 KB after the first run; the synthesizer is
deterministic. Swap the synthesized data for your own Hive-partitioned
Parquet tree to test against real data — the partition pattern in
`01-register.py` is the only thing that needs to change.

## Notes

- Install command sourced from
  [`<InstallMatrix />`](https://oz.com/docs/installation) — do not
  hand-roll.
- `oz-arcflow` is currently planned for PyPI (RAM-C2 / 2026-Q3). The
  cookbook pin describes the target end-state; running `uv sync` will
  fail until the wheel ships. Use the engine repo's `cargo` or
  `cargo install arcflow-core@0.8` (once the release workflow lands
  green) for the path that works today.

## See also

- [World Graph](/docs/concepts/layers/world-graph) — the
  conceptual layer this cookbook materialises against.
- [Perception Lake](/docs/concepts/layers/perception-lake) — the
  sibling layer that owns the immutable rows.
- [World Graph Substrate](/docs/architecture/worldgraph) — the
  engine-architecture deep-dive on the substrate underneath.
- [Causal Edges](/docs/concepts/causal-edges) — the discipline for
  values that influence belief, applicable to overlay tables when
  you need to correct a Lake-resident row.
