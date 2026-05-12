# Algo-Trading LLM Harness

**What you'll build:** A persistent, queryable, replayable market world-state
substrate that an LLM-driven trading stack uses as memory + orchestration
backbone. Three patterns the LLM-trading harness needs — demonstrated on
synthesized data using only shipped v1.6.7 APIs.

**Audience:** python, ml, agent, data-engineer.

**Runtime:** under 3 minutes total.

## Why this exists

Today's LLM-driven trading stacks bolt four silos together — vector DB,
SQL/timeseries store, message bus, scheduler — and pay the drift tax forever.
ArcFlow consolidates the four into one in-process graph (PAT-0013 SoC
monolith): persistent memory, maintained context, replayable audit, one
binary.

## The three steps

1. **`01-persistent-memory.py`** — `AS OF seq` replay. A mid-period earnings
   restatement lands as WAL seqs; the agent can read the *exact* fundamentals
   it saw at decision time. No look-ahead bias by construction. Bulk ingest
   vs `execute()` is the auditability boundary.
2. **`02-orchestrated-live-context.py`** — Three context queries (sector
   rollup, cross-sectional percentile rank, top-of-sector leader) re-read
   after a single new bar. The graph IS the orchestration substrate; the
   Python binding polls on tick (TS exposes `db.subscribe`).
3. **`03-confidence-weighted-fusion.py`** — Technical signals
   (`_observation_class: observed`, conf 0.95) and synthesized LLM-sentiment
   facts (`predicted`, conf 0.4–0.7) coexist in one graph. Same MATCH shape
   covers agreement, disagreement, and trust-tier filters.

## Run

```bash
uv sync
uv run python 01-persistent-memory.py
uv run python 02-orchestrated-live-context.py
uv run python 03-confidence-weighted-fusion.py
```

`_load.py` is the shared fixture: 8 symbols × 60 days OHLCV + fundamentals
(with a planted restatement landmine) + 6 synthesized sentiment events.

## Hidden features highlighted

- **`AS OF seq` counterfactual replay** — bit-for-bit reproducible memory.
- **Two-tier ingest** — `bulk_create_*` bypasses the WAL; `execute()` enters
  it. Cold history vs auditable decisions, one API choice.
- **Comma-`SET` granularity** — one WAL seq per assignment.
- **Window functions over graph properties** — `lag()`, `percent_rank()`,
  `row_number()` with `OVER (PARTITION BY … ORDER BY …)`.
- **`_observation_class` + `_confidence`** — the universal evidence-algebra
  columns. Same query shape spans observed, predicted, and disagreement.

## See Also

- [`temporal-counterfactual-replay`](../temporal-counterfactual-replay/) — `AS OF seq` patterns across fraud, robotics, IoT.
- [`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/) — confidence-weighted ER in a tracking domain.
- [`multi-stream-spatiotemporal-world-model`](../multi-stream-spatiotemporal-world-model/) — the multi-feed ingest + maintained-query pattern.
- Reference docs: [Temporal Queries](/temporal), [Confidence and Provenance](/concepts/confidence-and-provenance).
