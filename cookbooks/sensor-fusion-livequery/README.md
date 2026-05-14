# Multi-Sensor Fusion with Trust-Weighted Live Alerts

> **Fuse readings from multiple noisy sensors per entity, weight each
> by per-reading confidence, fire alerts only when the trust-weighted
> aggregate crosses a threshold — all as one query, polled on tick.**

**Audience:** python · ml · data-engineer
**Runtime:** ~1 minute
**Pins:** `oz-arcflow==0.7.2`

## The four hard problems this addresses

Multi-sensor fusion looks deceptively simple until you ship it to
production. Four engineering walls every team hits the moment the
number of sensors grows past one or two:

1. **Schema-divergent sensor streams.** Each sensor type (radar, lidar,
   camera, audio, vibration, temperature) has its own metadata, format,
   calibration parameters, and update cadence. The default architecture
   ships one table per sensor and a wide-join view trying to align
   them. The schema fights every time a sensor gets added or a
   calibration changes. The graph shape attaches each sensor reading
   as its own node with stream-local properties; the fusion query
   joins on the entity, not on a fragile pivoted view.

2. **Trust calibration lost across sensor boundaries.** Radar returns
   at 0.85 confidence; lidar at 0.92; camera at 0.78 with a
   weather-penalty modifier; vibration at 0.55 from a half-calibrated
   sensor. A fused alert ("contact detected") loses these confidence
   numbers unless the application carries them through every JOIN — at
   which point one schema change forgets the column and the agent
   stops being able to distinguish high-conviction from low. The graph
   carries `_confidence` on every reading edge; the trust-weighted
   aggregate IS the query.

3. **Live polling as the latency tax.** Sensor alerts want frame-time
   latency — fire when any sensor plus any cross-confirmation exceeds
   threshold. Re-running the fusion query on a timer re-traverses the
   whole sensor graph every tick. With dozens of sensors at 10–100 Hz,
   polling becomes the dominant CPU consumer of the pipeline. (Today's
   Python recipe uses this fallback; the Rust scaffold escapes to
   `CREATE LIVE VIEW` + `subscribe`.)

4. **Cross-sensor evidence isn't a JOIN.** *"Radar contact + lidar
   contact + camera contact within 2 m and 100 ms"* is a multi-stream
   temporal-spatial JOIN that takes longer to execute than the alert
   window it's protecting. Graph-shaped pattern matching does it in
   one MATCH against the entity that owns all the sensors.

Solving all four against one persistent, queryable graph with
`_observation_class` + `_confidence` on every reading is what this
recipe is for.

## What you'll build

1. **`00-make-sample.py`** — synthesizes `data/stream.parquet`: 3
   robots × 2 sensors (temperature, vibration) × 100 timesteps. Sensor
   2 on Robot R02 is deliberately noisier (mean confidence 0.55 vs
   0.92). One temperature anomaly is planted at frames 60–70 on R01 to
   make the trust-weighted alert fire.
2. **`02-load-stream.py`** — bulk-load the stream into ArcFlow's graph
   shape: `(:Robot)-[:HAS_SENSOR]->(:Sensor)-[:OBSERVED {value,
   _confidence, _observation_class, frame, _source}]->(:Reading)`.
3. **`03-trust-weighted-alerts.py`** — the fusion query. ArcFlow
   computes the confidence-weighted mean of sensor values per robot in
   one MATCH; the alert predicate is one extra WHERE clause.
4. **`04-live-polling.py`** — re-execute the fusion query on each new
   event window. The agent inspects the always-current answer. No
   subscription API in Python today; the API is `execute()`, the
   pattern is poll-on-event.
5. **`01-schema-design.md`** — reading-only: schema rationale.

## Run

```bash
uv sync
uv run python 00-make-sample.py     # synthesizes data/stream.parquet
uv run python 02-load-stream.py
uv run python 03-trust-weighted-alerts.py
uv run python 04-live-polling.py
```

## Capabilities exercised

| Capability | What it does for sensor fusion |
|---|---|
| `_observation_class` + `_confidence` on every Reading edge | Per-sensor trust calibration travels with the reading; one filter predicate covers every sensor type |
| Confidence-weighted aggregation in one query | Trust-weighted mean is `SUM(value × _confidence) / SUM(_confidence)` — one RETURN expression |
| `db.execute()` poll-on-event | The agent re-reads the standing fusion query on each new event window |
| Runtime introspection (`arcflow.__version__` / `ArcFlow.version()`) | Production health checks confirm the ArcFlow build the recipe is talking to. See [versioning](/docs/reference/versioning) |

## Rust SDK alongside

The `rust/` subfolder ships the same fusion recipe via the Rust SDK
plus the surface Python can't reach today: `CREATE LIVE VIEW
trust_weighted_alerts AS …` + `arcflow_sdk::subscribe(&db, view)`
replaces the polling fallback with maintained-result delta updates,
and `register_live_proof` attaches a continuous assertion that the
fusion view never goes empty (early-warning for sensor dropout).

## See also

- [`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/) — the substrate flagship; multi-stream sync at 60 Hz with auxiliary streams
- [`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/) — confidence-weighted entity resolution in a tactical-analytics domain
- [`algo-trading-world-model`](../algo-trading-world-model/) — the same evidence-algebra pattern applied to financial signals
