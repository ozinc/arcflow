# Spatiotemporal Tactical Queries

**What you'll build:** Three tactical query patterns over a small synthesized
spatiotemporal world model — counterfactual replay (`AS OF seq`),
confidence-weighted entity resolution across multiple ID namespaces, and
observed-vs-predicted fact fusion. Each pattern is one recipe step,
runnable in seconds.

**Audience:** python, data-engineer, ml, agent.

**Runtime:** under 1 minute total across all three steps.

**ArcFlow version:** 1.6.7.

## What this recipe is for

This is a **pattern catalog**, not an end-to-end pipeline. The
[`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/)
recipe covers ingest, identity reconciliation, multi-stream sync, LIVE
views, and triggers. This recipe sits on top: once your world model is
populated, what tactical queries do you actually run?

The three patterns chosen are the ones SQL handles awkwardly and ArcFlow
handles natively:

1. **Counterfactual replay** — `MATCH ... AS OF seq $param` reads the
   world model at a past WAL sequence number, exact and deterministic.
   Use cases: post-incident reconstruction, decision audit, comparing
   model predictions to the ground truth available at decision time.

2. **Confidence-weighted entity resolution** — entities are referenced by
   different identifiers across different sources (`id_a`, `id_b`,
   `id_c`). Cross-source matching is one extra `MATCH` clause; cross-
   source disagreement detection is the same shape with a confidence
   predicate. No JOIN chains, no COALESCE.

3. **Observed vs predicted facts** — every fact carries
   `_observation_class` (`observed`, `inferred`, `predicted`) and
   `_confidence`. Sensor readings, symbolic derivations, and neural-WM
   outputs coexist in one graph. Trust-tier filter is one `WHERE`
   predicate; calibration analysis chains observed → predicted via the
   shared entity.

## Run

```bash
uv sync
uv run python 01-counterfactual-replay.py
uv run python 02-confidence-entity-resolution.py
uv run python 03-observed-vs-predicted.py
```

`_load.py` is the shared synthesized fixture — 22 entities (alpha + beta
groups, 11 each), 60 frames at 60 Hz, two tracking sources with planted
disagreement on a known subset, a multi-namespace identity profile with
deliberate gaps and a collision, and a small set of predicted facts on
a future frame.

## Engine quirks observed during authoring (1.6.7)

These are honest notes for anyone running the recipe; each is filed as
an engine-repo issue, marked with `FIXME(arcflow-core#NNN)` annotations
in the script that hits it, and worked around inline.

| Issue | Quirk | Workaround |
|---|---|---|
| [#8](https://github.com/ozinc/arcflow-core/issues/8) | `walSeq()` returns the store's mutation counter, which advances on bulk_create_*; the WAL itself only sees `execute()` mutations. | Count `execute()` calls in your application to pick AS OF seqs. |
| [#9](https://github.com/ozinc/arcflow-core/issues/9) | Bulk_create_* operations preceding `execute()` SET mutations break AS OF replay — the SETs aren't reflected in temporal queries. | Use `execute()` throughout for the part of the workflow you want temporally queryable; bulk_create_* only for current-state-only fixture data. |
| [#10](https://github.com/ozinc/arcflow-core/issues/10) | Combining 3+ WHERE predicates spanning node + edge + Frame properties returns zero rows. | Use inline property predicates in the MATCH pattern. See `03-observed-vs-predicted.py`. |
| [#11](https://github.com/ozinc/arcflow-core/issues/11) | Arithmetic in `WITH` over property accessors errors with `EXPECTED_KEYWORD`. | Compute deltas in your application after pulling raw values, or stamp them onto edges at ingest time. |
| [#12](https://github.com/ozinc/arcflow-core/issues/12) | Python `None` in `bulk_create_nodes` props misaligns subsequent rows' property values (silent corruption). | Use a sentinel `""` (or any non-None scalar) and filter with `=` instead of `IS NULL`. |

All five are tracked engine-side and expected to land in the next minor.
When they ship, grep the recipe for `FIXME(arcflow-core#` to find every
workaround that can be removed.

## See Also

- [`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/) — the foundational ingest + LIVE-view recipe.
- [`sensor-fusion-livequery`](../sensor-fusion-livequery/) — standing-query pattern for live disagreement detection.
- [`fraud-graph-traversal`](../fraud-graph-traversal/) — confidence-weighted ER pattern in a different domain.
- Reference docs: [Temporal Queries](/temporal), [Confidence and Provenance](/concepts/confidence-and-provenance), [Built-in Functions](/worldcypher/functions/built-in).
