# Fraud Detection via Graph Traversal

> **Fan-out layering · fan-in concentration · multi-hop value chains —
> three classic AML patterns expressed as one-line graph queries instead
> of three self-joins each.**

**Audience:** python · data-engineer · compliance · ML engineer
**Runtime:** ~1 minute
**Pins:** `oz-arcflow==1.6.27`

A bank-transfer graph plus three pattern queries: fan-out (one source,
many recipients), fan-in (many sources, one beneficiary — the classic
mule pattern), and multi-hop value chains (`A → ? → ? → D` where each
leg moves a similar amount, the layering signal). Every query in the
recipe ships with its Neo4j Cypher equivalent in
`05-cypher-comparison.md` for analysts crossing from a Cypher-first
toolchain.

## The four hard problems this addresses

AML and fraud-detection workloads are graph problems wearing a tabular
disguise. The default stack — transfers in a relational table, alerts
in another, analyst notes in a third — ships four integration-tax
failures the moment the patterns get non-trivial:

1. **K-hop layering chains require K-1 self-joins in SQL.** A 4-hop
   `A → B → C → D` chain where each leg moves a similar amount is three
   self-joins, four WHERE clauses, and one near-exact-match join on
   amount. The query takes 10 minutes to write, deserves a sleepless
   review, and runs slowly against millions of transfers. The same
   chain in WorldCypher is one MATCH pattern. Adding a fifth hop is one
   character.

2. **Repetition is the fraud signal; rows-per-pair is the storage.** AML
   pipelines care about *patterns of repeated transfers* between the
   same accounts: twelve separate $9,800 transfers from twelve
   different mule accounts into one beneficiary. Stores that collapse
   to "one row per source-target pair, sum the amount" lose the count,
   the timing distribution, and the distinct-source-count that IS the
   signal. Modeling each transfer as its own node — not as an edge with
   an `amount` column — keeps every event distinct and queryable.

3. **Cross-engine semantics drift in production.** Analysts moving from
   Neo4j or another Cypher-first toolchain write queries in dialects
   that *almost* port. Subtle differences in path operators, DISTINCT
   semantics on relationships, and OPTIONAL MATCH behaviour produce
   wrong fraud-detection results that nobody notices until a regulator
   asks why a flagged transfer wasn't caught. Same query language,
   different engine, same answer is the only safe migration —
   `05-cypher-comparison.md` is the one-to-one mapping.

4. **Provenance for compliance audits.** Every fraud alert must trace
   back to the transfers that triggered it, the rule version that
   fired, and the analyst who reviewed. The default architecture (alert
   table + transfer table + audit log + rule registry) makes
   reconciliation under a regulator's gaze a forensics exercise.
   Storing the alert, the transfer chain, the rule version, and the
   analyst attribution as nodes + edges in one graph means the audit
   trail IS the queryable record.

Each one is solvable in isolation with enough engineering. Solving all
four against one persistent, queryable graph is what this recipe is for.

## What you'll build

1. **`02-load.py`** — bulk-ingest 220 transfers across 50 accounts from
   a Parquet file, modeling each transfer as a `Transfer` node between
   two `Account` nodes. Multiple transfers between the same pair coexist
   as distinct events.
2. **`03-fan-detection.py`** — fan-out and fan-in detection in single
   `MATCH … RETURN` queries with `count`-based filtering. No self-joins.
   The planted `SPLITTER-1` (fan-out, 9 recipients) and `MULE-1` (fan-in,
   12 sources) surface deterministically.
3. **`04-chain-detection.py`** — explicit K-hop MATCH chains for the
   layering pattern. The planted `LAYER-A → LAYER-B → LAYER-C → LAYER-D`
   four-hop chain with $9,500 ± noise per leg surfaces by a single
   pattern with three amount predicates.
4. **`01-fraud-patterns.md` + `05-cypher-comparison.md`** — reading-only:
   pattern catalogue + Neo4j-Cypher-vs-WorldCypher mapping for every
   query in the recipe.

## Run

```bash
uv sync
uv run python 00-make-sample.py     # synthesizes data/transfers.parquet
uv run python 02-load.py
uv run python 03-fan-detection.py
uv run python 04-chain-detection.py
```

`data/transfers.parquet` — 50 accounts, 220 transfers across two weeks,
three deliberately planted fraud patterns. Synthesized, deterministic,
~12 KB.

## Capabilities exercised

| Capability | What it does for fraud detection |
|---|---|
| Parquet bulk-load via `bulk_create_nodes` / `bulk_create_relationships` | 220 transfers ingest in milliseconds; scales to millions linearly |
| `MATCH (a)-[:SENT]->(t)-[:TO]->(b)` graph traversal | Fan-out, fan-in, multi-hop chains as single MATCH patterns |
| `count(*) AS n WHERE n >= threshold` aggregation | Concentration detection without self-joins |
| WorldCypher = Cypher-compatible | Drop-in for analysts coming from a Cypher-first toolchain |

## Rust SDK alongside

The `rust/` subfolder ships the same three pattern queries via the Rust
SDK, plus the Rust-only payoff: `register_skill` for live fraud alerts
that fire on every new `Transfer` mutation, and `LIVE CALL
algo.connectedComponents` for incremental mule-cluster detection
maintained as transfers arrive.

## See also

- [`temporal-counterfactual-replay`](../temporal-counterfactual-replay/) — `AS OF seq` for fraud-audit replay (what did the system see when this alert fired?)
- [`agent-knowledge-base`](../agent-knowledge-base/) — multi-hop entity traversal in a different domain
- [`from-sql-to-arcflow`](../from-sql-to-arcflow/) — the broader SQL-to-graph migration story
