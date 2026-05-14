# Spatiotemporal Tactical Queries

> **A pattern catalog: counterfactual replay (`AS OF seq`),
> confidence-weighted entity resolution across ID namespaces, and
> observed-vs-predicted fact fusion — each one a single recipe step.**

**Audience:** python · data-engineer · ml · agent
**Runtime:** under 1 minute total
**Pins:** `oz-arcflow==0.7.2`

This recipe is a pattern catalog, not an end-to-end pipeline. The
[`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/)
substrate flagship handles ingest, multi-stream sync, LIVE views, and
triggers. This recipe sits on top: once your world model is populated,
what tactical queries do you actually run?

## The four hard problems this addresses

Tactical analytics over a spatiotemporal world model is where most
default stacks discover their architecture limits. Four engineering
failures the patterns in this recipe make structurally impossible:

1. **Counterfactual replay against current-state-only stores.** Six
   weeks after an incident, the auditor asks *"what did the system see
   when it made that decision?"* Standard databases store current
   state only. Reconstructing the past requires correlating an audit
   log, a version table, and denormalized snapshots — three sources
   that drift the moment someone forgets to update one. `AS OF seq` is
   the same query language reading any past WAL sequence; one keyword,
   no separate audit infrastructure.

2. **Cross-namespace ER as a JOIN chain.** Entities arrive under
   different identifiers across different sources (`id_a`, `id_b`,
   `id_c`). The default architecture: a map table per pair of
   namespaces and a query that JOINs through them; cross-source
   disagreement detection adds another JOIN per source. Five sources
   = ten JOIN paths. The graph form: identifiers are properties on
   one Entity node; cross-source matching is one MATCH with a WHERE
   predicate on identifier sets.

3. **Confidence-weighted retrieval losing trust at the boundary.** A
   high-confidence sensor observation and a low-confidence model
   prediction look identical the moment they're projected into a
   tabular result — the trust tier was a column the JOIN forgot to
   carry. `_observation_class` + `_confidence` on every node and edge
   makes the trust tier as queryable as the value; trust-aware
   queries are one WHERE clause.

4. **Calibration analysis as a custom export pipeline.** Comparing
   predicted facts to the observations that eventually arrived
   ("model said target at (10, 20) confidence 0.6 — what was the
   actual position three frames later?") usually means dumping both to
   CSV and running pandas. In the graph it's a chain query: the same
   entity carries both the predicted and the observed fact; one MATCH
   joins them via the shared entity.

## Three patterns this recipe ships

1. **`01-counterfactual-replay.py`** — `MATCH … AS OF seq $param`
   reads the world model at a past WAL sequence number, exact and
   deterministic. Use cases: post-incident reconstruction, decision
   audit, comparing model predictions to the ground truth available at
   decision time.

2. **`02-confidence-entity-resolution.py`** — entities referenced by
   different identifiers across sources. Cross-source matching is one
   extra MATCH clause; cross-source disagreement detection is the same
   shape with a confidence predicate. No JOIN chains, no COALESCE.

3. **`03-observed-vs-predicted.py`** — sensor readings, symbolic
   derivations, and model-emitted facts coexist in one graph.
   Trust-tier filter is one WHERE predicate; calibration analysis
   chains observed → predicted via the shared entity.

## Run

```bash
uv sync
uv run python 01-counterfactual-replay.py
uv run python 02-confidence-entity-resolution.py
uv run python 03-observed-vs-predicted.py
```

`_load.py` — 22 entities (alpha + beta groups, 11 each), 60 frames at
60 Hz, two tracking sources with planted disagreement on a known
subset, a multi-namespace identity profile with deliberate gaps and a
collision, and a small set of predicted facts on a future frame.

## Capabilities exercised

| Capability | What it does for tactical analytics |
|---|---|
| `MATCH … AS OF seq $param … RETURN` | Replay the graph at any past WAL sequence — exact, deterministic, no separate audit table |
| Cross-namespace identifier matching as a MATCH predicate | Replaces N-table JOIN chains with one pattern |
| `_observation_class` + `_confidence` first-class | Trust-tier queries are one WHERE clause; calibration chains observed and predicted via the shared entity |
| One-graph fusion of observed / inferred / predicted | New signal sources land as more facts of the same shape — no schema migration |

## Rust SDK alongside

The `rust/` subfolder ships the same three patterns via the Rust SDK,
plus the Rust-only surface: `register_skill` on entity-resolution
mutations for live cross-source-disagreement alerts, and
`provenance_chain` walking the source attribution of any resolved
entity in one call.

## See also

- [`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/) — the foundational ingest + LIVE-view recipe this sits on top of
- [`team-sports-tactical-world-model`](../team-sports-tactical-world-model/) — tactical pattern detection (pressing, line-breaking, compression, counter)
- [`sensor-fusion-livequery`](../sensor-fusion-livequery/) — standing-query pattern for live disagreement detection
- [`temporal-counterfactual-replay`](../temporal-counterfactual-replay/) — focused `AS OF seq` replay across fraud, robotics, IoT
