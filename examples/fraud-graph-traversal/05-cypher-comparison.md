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

```cypher
MATCH (src:Account)-[:SENT]->(:Transfer)-[:TO]->(dst:Account)
RETURN dst.acct_id AS account, count(DISTINCT src) AS distinct_sources
ORDER BY distinct_sources DESC
LIMIT 5
```

Same shape in Neo4j Cypher.

## 2. Fan-out detection (splitters)

Mirror of fan-in: `src` ↔ `dst` swapped.

## 3. 4-hop value-conserving chain

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

For cases where the hop count is not known at authoring time, ArcFlow
exposes `shortestPath()` / `allShortestPaths()` — same shape as Neo4j.

## 4. Variable-length traversal

```cypher
MATCH (a:Account)-[:SENT|TO*1..6]->(b:Account)
WHERE a.acct_id = 'VICTIM-1'
RETURN a.acct_id, b.acct_id
```

Same syntax in Neo4j; both engines support `*N..M` quantifiers on labeled
relationships.

## Why graph at all

The chain query is the painful one in SQL. Finding "A → B → C → D where
each leg is between $9,000 and $10,000 and the whole sequence happens
inside one window" needs four self-joins on the transfers table, a
correlated subquery for the per-leg filter, and an ordered timestamp
predicate. In WorldCypher, it is one MATCH plus a Python filter — and
once the engine wave ships, just one MATCH.
