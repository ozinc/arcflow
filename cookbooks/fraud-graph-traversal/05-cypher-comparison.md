# Step 05 — ArcFlow ⇄ Neo4j Cypher Side-by-Side

For analysts moving between toolchains. Every query in this recipe has a
direct Neo4j Cypher equivalent. Both engines implement the
[GQL standard](https://www.gqlstandards.org/) (ISO/IEC 39075).

## Schema (both engines)

```cypher
(:Account {acct_id})
(:Transfer {transfer_id, amount, timestamp})
(:Account)-[:SENT]->(:Transfer)-[:TO]->(:Account)
```

## 1. Fan-in detection (mules)

### ArcFlow 1.6.6 (this recipe, step 03)

```cypher
MATCH (src:Account)-[:SENT]->(t:Transfer)-[:TO]->(dst:Account)
RETURN src.acct_id, dst.acct_id, t.amount
```

Distinct-source aggregation in Python. The recipe collects rows and tallies
client-side because `count(DISTINCT x)` is not yet stable in this engine wave.

### Neo4j Cypher

```cypher
MATCH (src:Account)-[:SENT]->(:Transfer)-[:TO]->(dst:Account)
RETURN dst.acct_id AS account, count(DISTINCT src) AS distinct_sources
ORDER BY distinct_sources DESC
LIMIT 5
```

Once the ArcFlow engine ships its `count(DISTINCT)` planner, the recipe
collapses to the same one-MATCH query.

## 2. Fan-out detection (splitters)

Same shape as fan-in, mirrored on `src` ↔ `dst`. Same engine constraint.

## 3. 4-hop value-conserving chain

### ArcFlow 1.6.6 (this recipe, step 04)

```cypher
MATCH (a:Account)-[:SENT]->(t1:Transfer)-[:TO]->(b:Account)
      -[:SENT]->(t2:Transfer)-[:TO]->(c:Account)
      -[:SENT]->(t3:Transfer)-[:TO]->(d:Account)
      -[:SENT]->(t4:Transfer)-[:TO]->(e:Account)
RETURN a.acct_id, b.acct_id, c.acct_id, d.acct_id, e.acct_id,
       t1.amount, t2.amount, t3.amount, t4.amount
```

Per-leg amount filter in Python. The engine enumerates chains; the recipe
filters them.

### Neo4j Cypher

```cypher
MATCH (a:Account)-[:SENT]->(t1:Transfer)-[:TO]->(b:Account)
      -[:SENT]->(t2:Transfer)-[:TO]->(c:Account)
      -[:SENT]->(t3:Transfer)-[:TO]->(d:Account)
      -[:SENT]->(t4:Transfer)-[:TO]->(e:Account)
WHERE t1.amount >= 9000 AND t1.amount <= 10000
  AND t2.amount >= 9000 AND t2.amount <= 10000
  AND t3.amount >= 9000 AND t3.amount <= 10000
  AND t4.amount >= 9000 AND t4.amount <= 10000
RETURN a.acct_id, e.acct_id, t1.amount, t2.amount, t3.amount, t4.amount
```

Cypher additionally supports `shortestPath()` and `allShortestPaths()` named-path
syntax for cases where the hop count is not known at query authoring time.
WorldCypher 1.6.6 does not yet expose those — the chain length must be explicit.

## 4. Variable-length traversal

### ArcFlow

```cypher
MATCH (a:Account)-[:SENT|TO*1..6]->(b:Account)
WHERE a.acct_id = 'VICTIM-1'
RETURN a.acct_id, b.acct_id
```

### Neo4j Cypher

Same syntax. Both engines support `*N..M` quantifiers on labeled
relationships.

## What is different in 1.6.6

| Concern | ArcFlow 1.6.6 | Neo4j 5.x |
|---|---|---|
| `MATCH ... RETURN ... ORDER BY ... LIMIT` | ✓ | ✓ |
| `count(x)`, `sum`, `avg`, `min`, `max` | ✓ | ✓ |
| `count(DISTINCT x)` | not yet shipped | ✓ |
| Single-WHERE on deeply-bound MATCH segment | ✓ | ✓ |
| Multi-WHERE on multiple deeply-bound segments | not yet shipped | ✓ |
| Variable-length `*N..M` | ✓ | ✓ |
| `shortestPath(...)` | not yet shipped | ✓ |
| `point({x, y})` + `distance(...)` | not yet shipped | ✓ (with spatial extension) |

The deltas listed as "not yet shipped" are tracked in the engine repo's
roadmap. This recipe runs entirely on `status: shipped` APIs at the
`meta.toml.manifest_pin` engine version.

## Why graph at all

The chain query is the painful one in SQL. Finding "A → B → C → D where
each leg is between $9,000 and $10,000 and the whole sequence happens
inside one window" needs four self-joins on the transfers table, a
correlated subquery for the per-leg filter, and an ordered timestamp
predicate. In WorldCypher, it is one MATCH plus a Python filter — and
once the engine wave ships, just one MATCH.
