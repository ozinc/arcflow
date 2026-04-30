# Multi-Sensor Fusion with Trust-Weighted Live Alerts

**What you'll build:** A live-polling sensor pipeline that fuses readings from
multiple noisy sensors per robot, weights each by per-reading confidence, and
fires alerts only when the trust-weighted aggregate crosses a threshold.

**Audience:** python, ml

**Runtime:** ~1 minute

**ArcFlow version:** 1.6.6

## Run

```bash
uv sync
uv run python 00-make-sample.py            # synthesizes data/stream.parquet
uv run python 02-load-stream.py
uv run python 03-trust-weighted-alerts.py
uv run python 04-live-polling.py
```

`01-schema-design.md` is a reading-only step.

## What this recipe demonstrates

1. **Confidence as a first-class property** — every sensor reading carries a
   `_confidence ∈ [0, 1]` on the edge. Queries filter and weight by it.
2. **Trust-weighted aggregation** — ArcFlow computes the confidence-weighted
   mean of sensor values per robot in one query.
3. **Live-polling pattern** — on each new event the agent re-executes the
   standing query and inspects the always-current answer. No subscription
   API; the API is `execute()`, the pattern is poll-on-event.
4. **Runtime introspection** — `ArcFlow.version()` reports the engine build
   the recipe is talking to (use this in production health checks).

## Data

`data/stream.parquet` — 3 robots × 2 sensors (temperature, vibration) × 100
timesteps = 600 readings. Sensor 2 on Robot R02 is noisier (`_confidence`
mean 0.55 vs 0.92). One temperature anomaly is planted at frame 60–70 on R01
to make the trust-weighted alert fire. Synthesized, deterministic, ~25 KB.

## Notes

- Pinned to ArcFlow 1.6.6 (see `meta.toml.manifest_pin`).
- Install command sourced from
  [`<InstallMatrix />`](https://oz.com/docs/installation) — do not hand-roll.
