# Step 03 — Coordinate Frames

Goal: understand why every stream declares its frame at ingest time, and
what ArcFlow refuses at the boundary (PAT-0035 hard contract).

## The three frames in this recipe

| Frame | Used by | Coordinates |
|---|---|---|
| `session-local` | tracking, scenes, events | x ∈ [0, 120], y ∈ [0, 80] (yards or metres — declared per session, not assumed) |
| `sensor-local` | biomechanical samples | gyro/accel/mag in the sensor's own basis (typically X-forward, Y-left, Z-up) |
| `master timecode` | every stream | `time_master_ns`: int64 nanoseconds from session start |

## Why we don't reconcile at ingest

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
   to apply blindly.** PAT-0035 records the frame so that consumers know
   what they're holding; query-time logic does the conversion when needed,
   with the frame metadata as input.

## What ArcFlow refuses at the boundary

PAT-0035 (Coordinate Frame Hard Contract) says: ArcFlow rejects mismatched
`metersPerUnit`, `upAxis`, or coordinate-system declarations at ingest with
a hard error. Never silent coercion, never default-correction.

The recipe's load script encodes this by:

- Tagging every per-stream node with `_source` (which sensor produced it)
  and (where applicable) `_coordinate_frame` (which basis the values are in).
- Letting query-time analytics decide whether to convert, when to convert,
  and what conversion to apply.

If a future contributor adds a stream with mismatched units, the load
script must declare the frame explicitly. CI rejects undeclared streams
through the cookbook coverage gate.

## The master timecode

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

## Stream-rate alignment

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

## Confidence per stream

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

## What's coming next

[`04-tracking-bulk-load.py`](./04-tracking-bulk-load.py) — the heavy lift,
60 Hz × 22 entities = 39,600 OBSERVED_AT edges plus the Frame.NEXT chain.

[`06-multi-stream-sync.md`](./06-multi-stream-sync.md) — the broader
discussion: video, audio, depth maps, eye tracking, force plates,
neural-network feature streams. How do they all hang on the canonical
timeline.
