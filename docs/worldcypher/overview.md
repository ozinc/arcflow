# WorldCypher Overview

WorldCypher is ArcFlow's query language — a Cypher-compatible language extended with spatial, temporal, reactive, and algorithmic capabilities.

If you know Cypher, you know WorldCypher. If you don't, it reads like ASCII art.

## Language structure

```
[clause] [pattern] [filter] [return] [modifiers]
```

Example:

```cypher
MATCH (p:Person)-[:KNOWS]->(f:Person)   -- pattern: find people who know people
WHERE p.age > 25                         -- filter: only those over 25
RETURN p.name, f.name                    -- return: project columns
ORDER BY p.name LIMIT 10                 -- modifiers: sort and limit
```

## Clauses

| Clause | Purpose | Example |
|---|---|---|
| `MATCH` | Find patterns | `MATCH (n:Person) RETURN n` |
| `CREATE` | Add data | `CREATE (n:Person {name: 'Alice'})` |
| `MERGE` | Find or create | `MERGE (n:Person {id: 'p1'})` |
| `SET` | Update properties | `SET n.age = 31` |
| `DELETE` | Remove nodes | `DELETE n` |
| `DETACH DELETE` | Remove nodes + edges | `DETACH DELETE n` |
| `REMOVE` | Remove a property | `REMOVE n.email` |
| `WITH` | Intermediate projection | `WITH n WHERE n.age > 25` |
| `UNWIND` | Expand a list | `UNWIND [1,2,3] AS x` |

## Extensions beyond Cypher

| Feature | Syntax | Description |
|---|---|---|
| Temporal snapshots | `AS OF 1700000000` | Query at a point in time |
| Reactive queries | `LIVE MATCH ...` | Standing queries that re-evaluate |
| Live algorithms | `LIVE CALL algo.pageRank()` | Incrementally maintained |
| Persistent views | `CREATE LIVE VIEW ...` | Named live query |
| Vector search | `CALL algo.vectorSearch(...)` | k-NN over embeddings |
| Full-text search | `CALL db.index.fulltext.queryNodes(...)` | BM25 scoring |
| Graph algorithms | `CALL algo.pageRank()` | 30+ algorithms, no projection setup |
| Multi-tenancy | `USE PARTITION 'ws-id'` | Tenant isolation |
| Session context | `SET SESSION ACTOR ...` | User/role binding |
| Skills | `CREATE SKILL ...` | Declarative AI skill |

## Detailed references

- [Spatial queries](spatial.md) — WITHIN, NEAR, distance functions
- [Temporal queries](temporal.md) — AS OF, time windows, trajectory
- [Algorithms](../reference/compatibility.md#algorithms-call-algo) — full algorithm list
- [Complete syntax](../reference/compatibility.md) — compatibility matrix
