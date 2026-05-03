# Multi-Stream Spatiotemporal World Model

**What you'll build:** A 60 Hz live world model from multi-entity tracking,
with auxiliary streams (3D scene reconstruction, high-rate biomechanical
telemetry, sparse event annotations) all reconciled to a single canonical
timeline. Then watch ArcFlow's LIVE views, standing queries, and behavior-
graph triggers maintain reactive analytics at the source cadence.

**Audience:** python, data-engineer, ml, agent.

**Runtime:** ~8 minutes.

**ArcFlow version:** 1.6.6.

## Why this recipe exists

This is the recipe for the use case ArcFlow's "world model database"
positioning was designed for: a real-time canonical timeline of tracked
entities in space, with multiple sensor streams running at different rates,
each carrying its own confidence and coordinate frame, all reconciled into
one queryable world.

The seed recipe ([`temporal-spatial-parquet-ingest`](../temporal-spatial-parquet-ingest/))
showed batch ingest of 10 Hz tracking. This recipe goes further:

- **60 Hz tick** — the standing-query update rate is sub-frame, the spatial
  index updates per-frame, the LIVE views maintain at the source cadence.
- **Multi-stream sync** — auxiliary streams (3D scene reconstructions, high-
  rate inertial telemetry, sparse event annotations) attach to the canonical
  timeline at their own rates.
- **Coordinate-frame discipline** — every stream declares its frame at
  ingest time; the engine refuses mismatches at the boundary
  (PAT-0035 hard contract).
- **Evidence + confidence per stream** — every fact carries
  `_observation_class` (`observed` / `inferred` / `predicted`) and
  `_confidence`. Trusted retrieval is a `WHERE r._confidence > 0.8` filter.
- **LIVE behavior** — `CREATE LIVE VIEW` for proximity / separation /
  formation; `CREATE TRIGGER` to fire behavior-graph SKILLs on every Frame.

## Run

```bash
uv sync
uv run python 00-make-sample.py
uv run python 02-identity-layer.py
uv run python 04-tracking-bulk-load.py
uv run python 05-multi-stream-attach.py
uv run python 07-spatial-queries.py
uv run python 08-temporal-queries.py
uv run python 09-live-views.py
uv run python 10-triggers-and-skills.py
uv run python 11-validate-internal.py
uv run python 12-replay-at-rate.py
```

`01-schema-design.md`, `03-coordinate-frames.md`, and `06-multi-stream-sync.md`
are reading-only steps — they walk through design choices.

## What this recipe demonstrates

1. **DDD schema for live tracking.** `Session` / `Entity` / `Frame` / `Stream`
   bounded contexts. Position lives on `OBSERVED_AT` edges (per-observation),
   not on `Entity` nodes (stable identity).
2. **60 Hz bulk load** of ~40K observations. `FlatSpatialIndex::bulk_load()`
   STR-pack ordering for the spatial layer. Shows throughput and the
   boundary between batch ingest and live-tick replay.
3. **Multi-stream attach.** A 3D scene-reconstruction stream at 30 Hz
   (one frame per two tracking frames). A 200 Hz biomechanical stream on
   one entity (one observation per ~0.3 tracking frames — denser than the
   canonical timeline). Each stream carries a coordinate-frame declaration
   and is reconciled to the canonical `Frame.timecode_master`.
4. **Spatial primitives** unique to ArcFlow: KNN, radius, bbox, geofence
   triggers — all over the live R*-tree spatial index.
5. **Temporal primitives**: per-entity trajectory via `Frame.NEXT` chain,
   LAG-style velocity windows, time-travel via `AS OF seq N`.
6. **LIVE views and behavior-graph triggers** at 60 Hz — sub-frame standing-
   query latency. The recipe replays ingest at the source cadence and shows
   LIVE views updating in real time.
7. **Validation invariants** without a reference engine. Counts and
   aggregates cross-checked between ArcFlow and the ground-truth ledger
   produced by the synthesizer (pyarrow/numpy only — no external DB).

## Data

`data/sample/` is generated at runtime by `00-make-sample.py`. ~30 seconds
of synthesized session at 60 Hz × 22 entities + 30 Hz auxiliary stream
+ 200 Hz biomechanical stream + sparse events. Total ~3 MB across 4
Parquet files. Deterministic (seeded RNG) — the synthesizer outputs
byte-equal Parquet on every run.

`data_provenance: synthesized` in `meta.toml`. No real customer data;
the shape mirrors common live-tracking domains (team sport, fleet
robotics, dense crowd analytics, motion capture).

## Adapting to your own data

Swap `data/sample/tracking.parquet` for your own per-frame tracking export
and adjust the schema mapping in `_load.py`. The recipe shape is
domain-agnostic: any
`(session_id, entity_id, frame_idx, time_master, x, y, z?, kinematics, confidence)`
shape works. The auxiliary streams (`scenes.parquet`, `imu.parquet`,
`events.parquet`) follow the same pattern — declare the rate, declare the
coordinate frame, attach to canonical Frames.

## Notes

- Pinned to ArcFlow 1.6.6 (see `meta.toml.manifest_pin`).
- During alpha, `oz-arcflow` resolves through OZ's PEP 503 simple index
  at `https://staging.oz.com/pypi/simple/`.
- The recipe deliberately uses **only ArcFlow + pyarrow + numpy** for
  validation — no external analytical engine. The point is that ArcFlow's
  built-in aggregates produce the same answers as the ground-truth ledger
  the synthesizer emits.
