# Step 01 — Fraud Patterns and Schema

Goal: name the three fraud patterns this recipe detects, and map them to
the chosen graph schema before writing any code.

## The data shape

Each row of `data/transfers.parquet`:

```
transfer_id, src_acct, dst_acct, amount, timestamp
```

220 transfers across 50 accounts over two weeks.

## Three fraud patterns

### 1. Fan-in concentration ("mule")

A single account receives many small payments from distinct sources over
a short window. The classic *money mule* — funds from multiple stolen
identities funneled to one drop account before exfiltration.

In our sample, `MULE-1` receives from 12 distinct accounts.

### 2. Fan-out layering ("splitter")

A single account sends many roughly-equal payments to distinct recipients.
The classic *layering* leg of money laundering — break a large sum into
smaller pieces routed through unrelated accounts to obscure provenance.

In our sample, `SPLITTER-1` sends to 9 distinct accounts.

### 3. Value-conserving chain

A multi-hop transfer chain where each leg passes approximately the same
amount: `A → B → C → D`, each leg ≈ $9,500. The hallmark of *placement*
in laundering — moving the same money through multiple intermediaries
to break the audit trail.

In our sample, `VICTIM-1 → LAYER-A → LAYER-B → LAYER-C → LAYER-D`
moves $9,500 ± $50 at each hop.

## The chosen schema

```cypher
(:Account {acct_id})
(:Transfer {transfer_id, amount, timestamp})
(:Account)-[:SENT]->(:Transfer)-[:TO]->(:Account)
```

Each transfer is its **own node**, not an edge property. Two reasons:

1. **Repeated transfers between the same accounts must remain distinct.**
   Modeling each transfer as a node keeps every event independently
   addressable, regardless of how the underlying engine deduplicates
   edge identity.

2. **Per-transfer attributes need a stable identity.** Timestamps,
   amounts, transfer ids, downstream evidence joins — all hang off the
   `Transfer` node, never off an edge.

## Why graph, not SQL

In SQL, all three patterns require self-joins:

- Fan-in / fan-out: `GROUP BY dst, COUNT(DISTINCT src)`.
- Chain detection: an N-way self-join, one per hop.

The chain query is the painful one. In SQL, finding "A → B → C → D where
each leg is between $9,000 and $10,000" needs four self-joins on the
transfers table, a correlated subquery for the per-leg filter, and an
ordered timestamp predicate. In WorldCypher, it is one MATCH.

The Neo4j Cypher equivalents are in `05-cypher-comparison.md`.

## Next

[`02-load.py`](./02-load.py) — load the Parquet into ArcFlow.
