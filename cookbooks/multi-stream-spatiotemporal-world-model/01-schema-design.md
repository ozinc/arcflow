# Step 01 — Schema Design

Goal: choose how multi-entity tracking + multi-stream auxiliary data lives
in ArcFlow before writing any load code. The right schema unlocks every
spatial and temporal primitive the engine ships; the wrong one boxes the
data into a flat table.

## The data shape

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

## The four bounded contexts

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
master timecode; coordinate-frame validation (PAT-0035) happens at attach
time; later queries don't need to know which stream came first.

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

## What we are NOT doing

- **Not** modelling 60 Hz Frame as a property bag on Session. That collapses
  the temporal axis into a list and breaks every per-frame query.
- **Not** putting position on the Entity node. That can't represent
  trajectories without secondary tables — and at that point the graph is a
  hash table.
- **Not** mixing streams of different rates into one wide row.
  `(frame, x, y, scene_uri, gyro_x, gyro_y, gyro_z, ...)` with NULLs
  everywhere is the relational anti-pattern the schema is built to avoid.
- **Not** carrying raw 3D scene blobs in graph properties. URIs only.

## Evidence layer

Every per-observation edge carries:

- `_observation_class`: `observed` (sensor measurement) | `inferred`
  (computed from observations) | `predicted` (forecast)
- `_confidence`: 0.0..1.0 — for tracking, derived from the per-frame
  data-quality index; for scenes, from reconstruction quality; for
  biomechanical samples, from the sensor's calibration metadata

Filter by trust: `WHERE r._confidence > 0.8 AND r._observation_class = 'observed'`.

## Coordinate frames

Three frames in this recipe; PAT-0035 enforces them:

- **session-local**: x ∈ [0, 120], y ∈ [0, 80], z optional. Tracking,
  scenes, events.
- **sensor-local**: gyroscope/accelerometer/magnetometer in the
  biomechanical sample's own basis. Reconciled to session-local at
  query time, not at ingest, so the raw sensor data stays auditable.
- **master timecode**: `time_master_ns` — int64 nanoseconds from session
  start. Every stream's native time stamp is mapped to master at attach
  time. Master is the single clock that joins everything.

## Next

[`02-identity-layer.py`](./02-identity-layer.py) creates the singleton
nodes (Session + Group + Sensor) and entity nodes. Tracking, scenes,
biomech, and events all attach in subsequent steps.
