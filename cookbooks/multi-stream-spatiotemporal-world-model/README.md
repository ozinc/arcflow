# Multi-Stream Spatiotemporal World Model

**What you'll build:** A 60 Hz live world model from multi-entity tracking,
with auxiliary streams (3D scene reconstruction, high-rate biomechanical
telemetry, sparse event annotations) all reconciled to a single canonical
timeline. Then watch ArcFlow's LIVE views, standing queries, and behavior-
graph triggers maintain reactive analytics at the source cadence.

**Audience:** python, data-engineer, ml, agent.

**Runtime:** ~30 seconds (load) plus a couple minutes for the per-step queries.

## What this recipe is for

A real-time canonical timeline of tracked entities in space, with multiple
sensor streams running at different rates, each carrying its own confidence
and coordinate frame, all reconciled into one queryable world.

- **60 Hz tick** — the standing-query update rate is sub-frame, the spatial
  index updates per-frame, the LIVE views maintain at the source cadence.
- **Multi-stream sync** — auxiliary streams (3D scene reconstructions, high-
  rate inertial telemetry, sparse event annotations) attach to the canonical
  timeline at their own rates.
- **Coordinate-frame discipline** — every stream declares its frame at
  ingest time; the engine refuses mismatched coordinate frames at ingest
  time, with a hard error rather than silent coercion.
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

The numbered Python steps run independently against the shared loader in
`_load.py`. Read the design discussion below before running them — schema
shape, coordinate-frame discipline, and multi-stream sync are the three
ideas the recipe is teaching.

## What this recipe demonstrates

1. **DDD schema for live tracking.** `Session` / `Entity` / `Frame` / `Stream`
   bounded contexts. Position lives on `OBSERVED_AT` edges (per-observation),
   not on `Entity` nodes (stable identity).
2. **60 Hz tracking ingest** of ~20K observations via the typed bulk APIs
   (`db.bulk_create_nodes` / `db.bulk_create_relationships`).
   Each observation lands as an
   `(:Entity)-[:OBSERVED_AT {x, y, z, _confidence, _observation_class}]->(:Frame)`
   edge. Position lives on the edge so the same Entity can be observed by
   multiple sensor streams independently. The bulk path bypasses the Cypher
   parser entirely — ~1M writes/sec sustained, the throughput floor for
   sensor-stream and batch-ingest workloads.

   **Indexes still recommended** for downstream `MATCH (n:Label {prop: val})`
   *query-time* lookups in steps 05 onwards: `:Entity(entity_id)`,
   `:Frame(frame_idx)`, and the auxiliary-stream join keys. The bulk-create
   path itself doesn't need them (it takes NodeIds directly), but query-time
   property lookups still benefit. See [Performance considerations](#performance-considerations).
3. **Multi-stream attach.** A 3D scene-reconstruction stream at 30 Hz
   (one frame per two tracking frames). A 200 Hz biomechanical stream on
   one entity (one observation per ~0.3 tracking frames — denser than the
   canonical timeline). Each stream carries a coordinate-frame declaration
   and is reconciled to the canonical `Frame.timecode_master`.
4. **Spatial primitives** unique to ArcFlow: KNN, radius, bbox, geofence
   triggers — all over the live R*-tree spatial index.

   ```cypher
   -- KNN: nearest entities to a point
   CALL algo.nearestNodes(point({x: 50.0, y: 25.0}), 'Entity', 5)
     YIELD node AS e, distance
   RETURN e.id, distance ORDER BY distance

   -- Radius: every entity within 10m of a point
   MATCH (e:Entity)-[r:OBSERVED_AT {frame_id: 'snap-7'}]->()
   WHERE distance(point({x: r.x, y: r.y}), point({x: 50.0, y: 25.0})) < 10.0
   RETURN e.id, r.x, r.y

   -- Bounding box: defenders inside a polygon at snap
   MATCH (snap:Frame {name: 'ball_snap'})
   MATCH (e:Entity {team: 'defense'})-[r:OBSERVED_AT]->(snap)
   WHERE r.x BETWEEN 40.0 AND 60.0
     AND r.y BETWEEN 20.0 AND 30.0
   RETURN e.id, r.x, r.y
   ```
5. **Temporal primitives**: per-entity trajectory via `Frame.NEXT` chain,
   LAG-style velocity windows, time-travel via `AS OF seq <literal>`. Note
   that `AS OF seq` currently accepts only literal integer seq values —
   variable bindings and expressions are not yet supported.
6. **LIVE views and behavior-graph triggers** at 60 Hz — sub-frame standing-
   query latency. The recipe replays ingest at the source cadence and shows
   LIVE views updating in real time.
7. **Validation invariants** without a reference engine. Counts and
   aggregates cross-checked between ArcFlow and the ground-truth ledger
   produced by the synthesizer (pyarrow/numpy only — no external DB).

## Schema design

The right schema unlocks every spatial and temporal primitive the engine
ships; the wrong one boxes the data into a flat table.

### The data shape

Three classes of input, each with its own native cadence:

| Stream | Cadence | Shape | Coordinate frame |
|---|---|---|---|
| Primary tracking | 60 Hz | `(session, entity, frame, x, y, z?, speed, accel, heading, orient, dqi)` | session-local |
| 3D scene reconstruction | 30 Hz | `(session, frame_master, scene_uri, scene_size_bytes, splat_count, sqi)` | session-local |
| High-rate biomechanical | 200 Hz | `(session, entity, t_unix_ns, gyro_xyz, accel_xyz, mag_xyz)` | sensor-local |
| Event annotations | sparse | `(session, frame_master, kind, payload_json)` | session-local |

Three different rates, three different coordinate frames (one nested
inside another), three different confidence signals. The schema must
reconcile them without hand-rolling timestamp math at every query.

### The four bounded contexts

```
                              Session (1)
                                  │
                                  │ TICKED_AT
                                  ▼
                           Frame (60 Hz × duration)
                ┌─────────────────┼──────────────────┐
                │ NEXT            │                  │
                ▼                 │                  │
            Frame'                │ OBSERVED_AT      │ ANCHORS
                                  ▼                  ▼
                              Entity              Event
                              (22 stable)         (sparse)
                                  ▲
                                  │ MEMBER_OF
                                  │
                                Group (2)


   Stream-attached state hangs off Frame:

   (Frame)─[:HAS_SCENE   {sqi}]──►(SceneReconstruction {uri, size, count})
   (Entity)─[:SAMPLED_AT {…}]───►(BiomechanicalSample {t_unix_ns, gyro, accel, mag})
                                   anchors: each sample carries
                                   pred_frame + next_frame for fast
                                   "what tracking frame surrounds this
                                   high-rate sample" lookups.
```

### Why this shape

**Frame is the canonical timeline.** Every stream attaches to Frame, even
streams that natively run at a different rate. The engine has a single
master timecode; coordinate-frame validation happens at attach time;
later queries don't need to know which stream came first.

**Position lives on the OBSERVED_AT edge, not the Entity node.** Entity is
stable identity (the same player across the entire session). Position is
per-observation. Position-on-edge means:

- per-frame snapshot is one MATCH on Frame
- per-entity trajectory is one MATCH along OBSERVED_AT ordered by Frame
- the spatial index (R*-tree) is over edge properties — KNN/radius queries
  resolve in sub-millisecond regardless of how many frames exist

**Auxiliary streams are nodes attached to Frame, not properties on Frame.**
3D scene reconstructions can be 5 MB per frame; you don't put that in a
property bag. You put a URI in a `SceneReconstruction` node and link
Frame→SceneReconstruction.

**Frame.NEXT is an explicit linked list.** Lets you ask
"what was the world 5 frames before `pass_arrived`?" without sorting at
query time, and powers `temporal.trajectory()` analytics natively.

**Group / Entity membership is temporal.** Per-session group membership
goes on `MEMBER_OF` edges with `_observation_class: 'observed'` and timing
metadata. The engine's WAL-sequenced storage means `AS OF seq N` queries
can ask "who was on which side at this moment?" The recipe is single-
session, but the schema is forward-compatible.

### What we are NOT doing

- **Not** modelling 60 Hz Frame as a property bag on Session. That collapses
  the temporal axis into a list and breaks every per-frame query.
- **Not** putting position on the Entity node. That can't represent
  trajectories without secondary tables — and at that point the graph is a
  hash table.
- **Not** mixing streams of different rates into one wide row.
  `(frame, x, y, scene_uri, gyro_x, gyro_y, gyro_z, ...)` with NULLs
  everywhere is the relational anti-pattern the schema is built to avoid.
- **Not** carrying raw 3D scene blobs in graph properties. URIs only.

### Evidence layer

Every per-observation edge carries:

- `_observation_class`: `observed` (sensor measurement) | `inferred`
  (computed from observations) | `predicted` (forecast)
- `_confidence`: 0.0..1.0 — for tracking, derived from the per-frame
  data-quality index; for scenes, from reconstruction quality; for
  biomechanical samples, from the sensor's calibration metadata

Filter by trust: `WHERE r._confidence > 0.8 AND r._observation_class = 'observed'`.

## Coordinate frames

Three frames in this recipe; the engine enforces them at ingest:

| Frame | Used by | Coordinates |
|---|---|---|
| `session-local` | tracking, scenes, events | x ∈ [0, 120], y ∈ [0, 80] (yards or metres — declared per session, not assumed) |
| `sensor-local` | biomechanical samples | gyro/accel/mag in the sensor's own basis (typically X-forward, Y-left, Z-up) |
| `master timecode` | every stream | `time_master_ns`: int64 nanoseconds from session start |

### Why we don't reconcile at ingest

The naive shape: convert biomechanical samples from sensor-local to
session-local at ingest time, write the rotated values, throw away the
raw axes. The graph then has "everything in one frame," superficially clean.

We don't do this. The recipe stores raw sensor-local IMU axes and carries
`_coordinate_frame: 'sensor-local'` on the BiomechanicalSample node. The
reasons:

1. **Auditability.** When a downstream calibration question arises ("was
   the IMU drift compensated for at sample 4823?"), the raw axes are still
   there. Rotated-then-discarded is not recoverable.
2. **Calibration is a function of the entity, not the sample.** The same
   sensor on a different mounting produces a different rotation. Storing
   per-sample rotated values bakes the mounting in.
3. **Coordinate frame is metadata about the value, not a transformation
   to apply blindly.** Recording the frame on the stream node lets
   consumers know what they're holding; query-time logic does the
   conversion when needed, with the frame metadata as input.

### What ArcFlow refuses at the boundary

ArcFlow rejects mismatched `metersPerUnit`, `upAxis`, or coordinate-system
declarations at ingest with a hard error. Never silent coercion, never
default-correction.

The recipe's load script encodes this by:

- Tagging every per-stream node with `_source` (which sensor produced it)
  and (where applicable) `_coordinate_frame` (which basis the values are in).
- Letting query-time analytics decide whether to convert, when to convert,
  and what conversion to apply.

If a future contributor adds a stream with mismatched units, the load
script must declare the frame explicitly. CI rejects undeclared streams
through the cookbook coverage gate.

### The master timecode

`time_master_ns` is the single clock every stream maps to at attach time.
Stream-native time stamps stay on the stream's nodes (e.g.
`BiomechanicalSample.t_unix_ns` — the absolute sensor clock), but the
master is what joins everything.

Master is **session-relative int64 nanoseconds from frame 0**. This is:

- Tick-accurate for any rate up to 1 GHz
- Free of timezone, leap-second, and clock-skew ambiguity
- Trivially convertible: `t_master_ns / 10^9` → seconds, `t_master_ns * 60 / 10^9` → 60 Hz frames
- Rate-agnostic: a 30 Hz scene stream and a 200 Hz IMU stream both map cleanly

For sessions that span clock boundaries (long-running, distributed, or
across daylight-saving transitions), master is what stays sane while
wall-clock representations vary.

### Stream-rate alignment

| Stream rate | Alignment to canonical 60 Hz Frame |
|---|---|
| 60 Hz tracking | 1:1 — tracking edge directly to Frame at index `f` |
| 30 Hz scene | 2:1 — scene attaches to Frame at index `f * 2` (every other Frame) |
| 200 Hz biomech | 1:3.33 — sample carries `pred_frame` + `next_frame` (floor + ceil) |
| Sparse events | event attaches to nearest Frame at the event's `time_master_ns` |

All three patterns coexist in the schema. None of them require a join
table or special query syntax — `(Entity)-[:OBSERVED_AT]->(Frame)` and
`(Frame)-[:HAS_SCENE]->(SceneReconstruction)` and
`(Entity)-[:SAMPLED_AT]->(BiomechanicalSample)` are first-class graph
edges that compose freely.

### Confidence per stream

Every stream's per-observation confidence has a different origin:

- Tracking `_confidence = dqi`: positional accuracy reported by the sensor
  per frame. Drops on occluded frames.
- Scene `_confidence = sqi`: reconstruction quality. Drops on occluded or
  fast-motion frames.
- Biomech `_confidence`: sensor calibration metadata + drift over time.
  Recipe uses a placeholder constant; in production this comes from the
  sensor's per-sample QI signal.

The unification: every fact in the graph carries `_confidence` (0.0..1.0)
and `_observation_class` (`observed` | `inferred` | `predicted`).
Trust-aware queries are a `WHERE r._confidence > 0.8` filter, regardless
of stream.

## Multi-stream sync — the broader pattern

The 60 Hz tracking + 30 Hz scene + 200 Hz biomech + sparse-event shape
used here generalises to almost every modern AI / AR / autonomy /
sports-analytics / robotics / HCI / motion-capture workload.

A real-world session produces multiple time-coded streams, each with
different cadence, fidelity, coordinate frame, and confidence. Examples
that follow the same shape as this recipe:

| Stream class | Typical rate | Lives at | Coordinate frame |
|---|---|---|---|
| Real-time tracking (RTLS, GPS, vision) | 5–60 Hz | per-frame edges to Frame | session-local |
| Video frames (RGB) | 24 / 30 / 60 / 120 fps | per-frame `VideoFrame` node, URI | camera-local → session-local at calibration |
| Depth / RGBD | 24–60 fps | per-frame `DepthFrame` node | camera-local |
| 3D scene reconstruction (e.g. neural rendering) | 1–30 Hz | per-frame node carrying URI to reconstruction blob | world-local |
| Skeletal motion capture | 60–240 Hz | per-frame skeleton node, joint-rotation arrays | mocap-rig-local |
| Inertial telemetry (gyro + accel + mag) | 100–1000 Hz | dense `BiomechanicalSample` nodes | sensor-local |
| Eye tracking | 60–1000 Hz | per-sample gaze node | head-local |
| Force plates / haptic sensors | 1000+ Hz | dense sample nodes | platform-local |
| Audio | 16–96 kHz | continuous segments anchored to time spans, blob URIs | session-local |
| Neural-network feature streams (embeddings, detections, classifications) | variable | per-inference node anchored to source frame | model-internal |
| Event annotations (semantic / coach / referee / human) | sparse | `Event` nodes anchored to nearest Frame | session-local |

The unifying observation: **every stream is "something happens at a time
in a coordinate frame, with a confidence."** ArcFlow's schema reflects
that exactly:

- Every stream attaches to the canonical Frame timeline (`time_master_ns`)
- Every per-observation node/edge carries `_observation_class` +
  `_confidence` + `_source`
- Coordinate-frame metadata travels with the value, never silently
  converted

### Rate alignment patterns

Three patterns cover everything:

#### 1. Lower-rate stream (1:N alignment)

The 30 Hz scene stream attaches every 2nd 60 Hz Frame:

```
Frame[0]──HAS_SCENE──Scene[0]
Frame[1]
Frame[2]──HAS_SCENE──Scene[1]
Frame[3]
Frame[4]──HAS_SCENE──Scene[2]
...
```

Query "what scene was active at Frame 17?":

```cypher
MATCH (f:Frame {frame_idx: 17}) OPTIONAL MATCH (f0:Frame {frame_idx: 16})-[:HAS_SCENE]->(s)
RETURN s.scene_uri
```

Or the more general "valid until next observation" semantics: the most
recent prior scene attachment.

#### 2. Higher-rate stream (1:N alignment, dense)

The 200 Hz biomech stream produces ~3.33 samples per 60 Hz Frame. Each
sample carries `pred_frame` + `next_frame` (floor + ceil canonical Frame
indices) so "biomech samples between Frame N and Frame N+1" is a property
range scan:

```cypher
MATCH (e:Entity {entity_id: 'alpha-00'})-[:SAMPLED_AT]->(b:BiomechanicalSample)
WHERE b.pred_frame >= 17 AND b.pred_frame < 18
RETURN b.t_unix_ns, b.gyro_x, b.gyro_y, b.gyro_z
ORDER BY b.t_unix_ns
```

#### 3. Sparse stream (point alignment)

Events anchor to the nearest Frame at `time_master_ns`. A single edge
`(Event)-[:ANCHORED_AT]->(Frame)`. Queries compose freely:

```cypher
MATCH (ev:Event {kind: 'phase_change'})-[:ANCHORED_AT]->(f:Frame)
MATCH (e:Entity)-[r:OBSERVED_AT]->(f)
RETURN e.entity_id, r.x, r.y
```

Ask "where was every entity at the moment of this event?" — one MATCH
chain, no time arithmetic.

### Confidence layer (across streams)

Every observation edge / node carries `_confidence: 0.0..1.0`. The origin
of the score depends on the stream:

| Stream | `_confidence` source |
|---|---|
| Tracking | per-frame data quality / signal strength / occlusion score |
| Scene | reconstruction quality (residual error, splat stability) |
| Video | encoder QP, motion blur estimation, focus measure |
| Biomech | sensor calibration metadata + drift over time |
| Eye tracking | pupil-detection confidence, head-mounted IMU coupling |
| ML inference | model output confidence (softmax, entropy, ensemble variance) |
| Human annotation | annotator agreement (inter-rater reliability) |

The unification is: any downstream query can ask "trust ≥ X" with the
same `WHERE r._confidence > X` filter, regardless of which stream
provided the observation. **Trusted retrieval becomes a single query
predicate, not a per-stream pipeline.**

### What ArcFlow brings to the multi-stream pattern

1. **Single canonical timeline.** Every stream lives on one Frame
   timeline; cross-stream queries are graph traversals, not joins on
   timestamp ranges.
2. **Spatial index over per-observation values.** Position lives on
   edges, the R*-tree is over edge properties, KNN/radius queries
   resolve in sub-millisecond regardless of how many streams contribute.
3. **Standing queries / LIVE views.** A query maintained at the source
   tick rate. At 60 Hz tick, LIVE views update every 16.67 ms; at 1 kHz
   biomech tick, the engine fires on every sample.
4. **Confidence-aware retrieval as a first-class filter.** Trusted RAG,
   evidence algebra, certainty-aware fusion — all built on
   `_confidence` + `_observation_class` + Z-set weights.
5. **Time travel.** WAL-sequenced storage means `AS OF seq N` queries
   reproduce the world's state at any past tick across all streams,
   atomically.
6. **No external orchestration.** Every primitive (event detection,
   formation classification, anomaly flagging, multi-rate fusion) lives
   in-process. No Kafka, no Flink, no per-stream microservice.

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

## Performance considerations

**This recipe runs on a synthesized 30-second sample (~20K observations,
~22 entities). The bulk APIs land the entire load in ~0.5 seconds on a
single thread.**

Production-scale workloads (a full session of millions of edges across
hundreds of entities) follow the same pattern — only the multipliers grow.
Three perf primitives carry the weight:

### 1. `bulk_create_nodes` / `bulk_create_relationships` — for ingest

Per-row `MATCH+CREATE` round-trips the parser at ~3–10K writes/sec and
decays under graph growth. The bulk-array path bypasses the parser
entirely and writes at ~1M ops/sec — a single tracking session of ~1M
`OBSERVED_AT` edges loads in seconds.

```python
# Old shape (per-row, parser-bound):
for r in rows:
    db.execute(f"MATCH (e:Entity {{id: {r['eid']}}}), (f:Frame {{id: {r['fid']}}}) "
               f"CREATE (e)-[:OBSERVED_AT {{seq: {r['seq']}}}]->(f)")

# New shape (bulk, parser-free):
ents = db.bulk_create_nodes([(["Entity"], {"id": e}) for e in entities])
fids = db.bulk_create_nodes([(["Frame"], {"id": f}) for f in frames])
db.bulk_create_relationships(
    "OBSERVED_AT",
    [(ents[r["eid"]], fids[r["fid"]], {"seq": r["seq"]}) for r in rows],
)
```

CREATE semantics — every call allocates a new edge. Use Cypher `MERGE` if
you need find-or-create.

### 2. `result.to_arrow()` — for reads

Materializing a 1M-row `MATCH ... RETURN` as `list[dict]` pays per-row
Python object cost AND loses types (every cell becomes a string).
`result.to_arrow()` hands typed Arrow buffers zero-copy:

```python
tbl = db.execute("MATCH (e)-[r:OBSERVED_AT]->(f) "
                 "RETURN e.entity_id, r.x, r.y, r.speed").to_arrow()
# pyarrow.RecordBatch — typed columns, ready for pandas/polars/duckdb.

import polars as pl
df = pl.from_arrow(tbl)

# Or directly into DuckDB for fast SQL analytics:
import duckdb
duckdb.connect().register("obs", tbl).execute(
    "SELECT entity_id, AVG(speed) FROM obs GROUP BY entity_id"
).fetchall()
```

Per-column types are honored (Int → int64, Float → float64, String → utf8,
Bool → bool, list-typed properties → typed Arrow lists). 18.8× faster than
`list(result)` on 50K-row reads in benchmarks.

### 3. Threading concurrency — `concurrent.futures` works

ctypes releases the GIL for every native call; `ConcurrentStore` is
MVCC-safe for parallel readers. Multiple Python threads on one ArcFlow
instance run in real parallel:

```python
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(db.execute, queries))
# 4.75× speedup with 8 threads on M1 (8-core).
```

Reads parallelize cleanly; writes serialize through MVCC commit (no
deadlock, no torn rows).

Spatial KNN / radius / bbox queries resolve through the R*-tree on edge
properties and stay sub-millisecond regardless of database size — that
path is independent of the bulk-create / Arrow paths above.

## Notes

- `oz-arcflow` resolves through OZ's PEP 503 simple index at
  `https://staging.oz.com/pypi/simple/`.
- The recipe deliberately uses **only ArcFlow + pyarrow + numpy** for
  validation — no external analytical engine. The point is that ArcFlow's
  built-in aggregates produce the same answers as the ground-truth ledger
  the synthesizer emits.
