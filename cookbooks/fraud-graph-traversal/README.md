# Fraud Detection via Graph Traversal

**What you'll build:** A bank-transfer graph in ArcFlow, then three classic
graph-native fraud queries — fan-out layering, fan-in concentration,
multi-hop value chains — alongside the equivalent Neo4j Cypher for
direct comparison.

**Audience:** python, data-engineer

**Runtime:** ~1 minute

**ArcFlow version:** 1.6.6

## Run

```bash
uv sync
uv run python 00-make-sample.py            # synthesizes data/transfers.parquet
uv run python 02-load.py
uv run python 03-fan-detection.py
uv run python 04-chain-detection.py
```

`01-fraud-patterns.md` and `05-cypher-comparison.md` are reading-only steps.

## What this recipe demonstrates

1. **Transfer-as-node schema** — modeling each transfer as a `Transfer`
   node between two `Account` nodes lets multiple transfers between the
   same accounts coexist as distinct events. Crucial for AML pipelines
   where repetition is the signal.
2. **Fan-out / fan-in detection** — outdegree and indegree become single
   `MATCH ... GROUP BY` queries. No self-joins.
3. **Multi-hop layering chains** — explicit K-hop MATCH chains find
   `A → ? → ? → D` flows where each leg moves a similar amount. Direct
   in graph terms; painful in SQL.
4. **Cross-engine semantics** — every query in this recipe has its
   Neo4j Cypher equivalent in `05-cypher-comparison.md` so an analyst
   moving from a Cypher-first toolchain has a one-to-one mapping.

## Data

`data/transfers.parquet` — 50 accounts, 220 transfers across two
weeks. Three fraud patterns are planted:

- **MULE-1** (fan-in): `MULE-1` receives from 12 distinct sources.
- **LAYER-A → LAYER-B → LAYER-C → LAYER-D** (chain): four hops, each
  passing $9,500 ± noise.
- **SPLITTER-1** (fan-out): `SPLITTER-1` sends to 9 distinct recipients.

Synthesized, deterministic, ~12 KB.

## Notes

- Pinned to ArcFlow 1.6.6 (see `meta.toml.manifest_pin`).
- Install command sourced from
  [`<InstallMatrix />`](https://oz.com/docs/installation) — do not hand-roll.
