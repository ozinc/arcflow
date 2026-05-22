# Step 01 — Schema Design

Goal: choose how multi-sensor readings live in ArcFlow before writing any code.

## The data shape

Each row of `data/stream.parquet`:

```
timestamp, frame_id, robot_id, sensor_id, modality, value, confidence
```

Three robots, two sensors per robot, 100 frames at 10 Hz. 600 rows total.

## The chosen schema

```cypher
(:Robot  {robot_id})
(:Sensor {sensor_id, robot_id, modality}) -[:MOUNTED_ON]-> (:Robot)
(:Frame  {frame_id, timestamp})
(:Sensor)-[:READ {value, confidence}]->(:Frame)
```

- `Robot` and `Sensor` are stable identities (low cardinality).
- `Frame` is one node per timestamp, shared across all sensors observing
  that frame. This makes "everyone reading at frame 65" a one-MATCH query.
- `READ` is the per-frame observation edge. The `(Sensor, Frame)` pair is
  unique — one edge per measurement.

## Why confidence is on the edge

A sensor's mean confidence band tells you *which sensors to trust on
average*. The per-reading confidence tells you *which individual frames
to trust*. Production fusion pipelines fail when those two are conflated:
one bad frame from a generally-good sensor can dominate the average if
its confidence is treated as 1.0.

ArcFlow's stance: every observation edge carries `confidence`. Queries
either filter (`WHERE r.confidence > 0.7`) or weight (`sum(r.value *
r.confidence) / sum(r.confidence)`) — both are pure WorldCypher.

## Why Frame is its own node

Two reasons:

1. **Edge identity.** The shipped engine treats `(Sensor)-[:READ]->(Robot)`
   as one edge per `(Sensor, Robot)` pair regardless of how many CREATEs you
   issue. Anchoring the edge to a per-timestamp `Frame` node makes every
   reading a distinct edge: 6 sensors × 100 frames = 600 unique pairs.

2. **Cross-sensor fusion** — multiple sensors observing the *same* frame
   join through the shared `Frame` node. That is the canonical way to
   express "fuse all readings of frame 65 across sensors" in WorldCypher.

## What we are NOT doing

- Storing the latest reading on the Robot node. That collapses time and
  destroys the ability to do trust-weighted aggregates over a window.
- Modelling each frame as a row attached only to a single sensor. That
  would prevent cross-sensor joins through the frame.

## Next

[`02-load-stream.py`](./02-load-stream.py) — bulk load the Parquet stream
into ArcFlow.
