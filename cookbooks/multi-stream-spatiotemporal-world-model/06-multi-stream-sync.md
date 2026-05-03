# Step 06 — Multi-Stream Sync (the big idea)

Goal: situate this recipe in the broader pattern of multi-stream
spatiotemporal data. The 60 Hz tracking + 30 Hz scene + 200 Hz biomech +
sparse-event shape used here generalises to almost every modern AI / AR /
autonomy / sports-analytics / robotics / HCI / motion-capture workload.

## The pattern

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
  converted (PAT-0035)

## The master timecode

A canonical `time_master_ns` (int64 nanoseconds from session start) is
the single clock every stream maps to. Each stream's native time stamp
stays on the stream's nodes — it's the master that joins.

**Why nanoseconds, not seconds or ms?** Audio is the limit case: 96 kHz
audio is one sample per ~10.4 µs. Microsecond resolution covers
everything except the highest-rate scientific sensors; nanoseconds give
six orders of magnitude of headroom and avoid float drift across long
sessions.

**Why session-relative, not Unix epoch?** Sessions span clock boundaries
(daylight-saving transitions, leap seconds, distributed-clock skew). A
session-relative master stays sane while wall-clock representations
vary; the wall-clock origin is a single field on the Session node.

## Rate alignment patterns

Three patterns cover everything:

### 1. Lower-rate stream (1:N alignment)

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

### 2. Higher-rate stream (1:N alignment, dense)

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

### 3. Sparse stream (point alignment)

Events anchor to the nearest Frame at `time_master_ns`. A single edge
`(Event)-[:ANCHORED_AT]->(Frame)`. Queries compose freely:

```cypher
MATCH (ev:Event {kind: 'phase_change'})-[:ANCHORED_AT]->(f:Frame)
MATCH (e:Entity)-[r:OBSERVED_AT]->(f)
RETURN e.entity_id, r.x, r.y
```

Ask "where was every entity at the moment of this event?" — one MATCH
chain, no time arithmetic.

## Coordinate-frame discipline

Every value lives in a frame. The recipe shows three; production systems
typically have five to ten. The discipline:

- **Declare at ingest time.** Every stream's nodes carry
  `_coordinate_frame` (or the frame is implied by `_source` plus a
  per-source frame manifest in the Session).
- **Don't silently convert.** Storing rotated-and-discarded raw values
  destroys auditability. Store the raw values + frame metadata; convert
  at query time when the answer requires it.
- **Reject mismatches at the boundary.** PAT-0035 hard contract: ArcFlow
  refuses ingestion when a declared frame conflicts with a session
  frame manifest (units mismatch, axis convention mismatch, etc.).

## Confidence layer

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

## What ArcFlow brings to the multi-stream pattern

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
   `_confidence` + `_observation_class` + Z-set weights (PAT-0021,
   PAT-0023).
5. **Time travel.** WAL-sequenced storage means `AS OF seq N` queries
   reproduce the world's state at any past tick across all streams,
   atomically.
6. **No external orchestration.** Every primitive (event detection,
   formation classification, anomaly flagging, multi-rate fusion) lives
   in-process. No Kafka, no Flink, no per-stream microservice.
   See ANTI-0014.

## What's coming next

[`07-spatial-queries.py`](./07-spatial-queries.py) — KNN, radius, geofence
over the live R*-tree.

[`08-temporal-queries.py`](./08-temporal-queries.py) — LAG-style velocity,
trajectory queries, time travel.

[`09-live-views.py`](./09-live-views.py) and
[`10-triggers-and-skills.py`](./10-triggers-and-skills.py) — the reactive
layer: standing queries that maintain at 60 Hz tick, behavior-graph
SKILLs that fire on Frame creation.

[`12-replay-at-rate.py`](./12-replay-at-rate.py) — the punchline. Replay
ingest at the source cadence and watch LIVE views update in real time.
