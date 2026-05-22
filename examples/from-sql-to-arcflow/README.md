# From SQL to ArcFlow

> **Three side-by-side comparisons: same data, same question, same
> answer — DuckDB SQL on one side, WorldCypher on the other.**

A migration on-ramp for engineers with SQL muscle memory who are
evaluating ArcFlow for graph-shaped questions. No marketing — same
inputs, same outputs, the queries themselves are the comparison.

**Audience:** python · data-engineer · sql-user
**Runtime:** under 1 minute total
**Pins:** `oz-arcflow==0.8.0`

## The four hard problems this addresses

A team with years of SQL muscle memory has earned the right to evaluate
a graph database by the queries it would actually run, not by
benchmark theatre. Four migration-tax failures the side-by-side makes
concrete:

1. **K-hop queries explode into K-1 self-joins in SQL.** *"People
   within 2 hops of Alice who've worked in biotech"* in DuckDB is
   five CTEs and a hard-coded path depth; extending to 3 hops means
   rewriting the query, extending to N hops needs a recursive CTE that
   traditional optimizers struggle with. In WorldCypher, one MATCH
   pattern; the hop depth is one character.

2. **Schema rigidity vs evolving relationships.** SQL bakes
   relationships into table layout via foreign keys — adding a new
   relationship type means a new table and an ALTER cascade through
   every dependent query. ArcFlow stores relationships as first-class
   edges with their own properties — a new relationship type is a new
   label, not a schema migration.

3. **Confidence-aware retrieval needs a parallel pipeline.** SQL stores
   confidence as a column on the row. Filtering by confidence is one
   `WHERE` clause, but *propagating confidence through joins* — the
   confidence-weighted PageRank or path query — requires custom SQL
   plus application-layer logic, or a separate graph store the analyst
   keeps in sync. The integration tax surfaces every time someone
   refactors. In ArcFlow, `_confidence` lives on every node and edge;
   the same column powers a `WHERE` filter and `algo.confidencePageRank`.

4. **The query-language switch is the actual migration cost.** Moving
   from SQL to a graph engine that requires learning a fundamentally
   different dialect is a multi-quarter exercise. Moving to one that
   speaks BOTH SQL (over the PostgreSQL wire protocol) AND a graph
   language for graph-shaped questions is two days. `psql`, DBeaver,
   `sqlx`, and any PG-wire client connect to ArcFlow directly. The
   recipe shows the graph-shaped wins; the wire compatibility means the
   team keeps their SQL toolchain for the queries where it already
   wins.

Each problem is solvable in isolation with enough engineering. Avoiding
all four against the same database is what this migration on-ramp is
for.

## What you'll build

Three side-by-side comparisons. Each step loads the *same* fixture into
both DuckDB and ArcFlow and prints both queries plus the (identical)
results so the reader can compare shape and verdict at a glance.

| Step | Question | Verdict |
|---|---|---|
| `01-shared-coworkers.py` | "Who has worked at the same company as Alice?" | Cypher walks one edge; SQL needs four self-joins. |
| `02-confidence-tiered-query.py` | "Employment relationships with confidence > 0.85" | A flat filtered projection in either engine. The lift compounds the moment confidence-aware algorithms consume the same `_confidence` column natively. |
| `03-multi-hop-industry.py` | "People within 2 hops of Alice who've worked in biotech" | SQL: five CTEs + hard-coded depth. Cypher: one MATCH chain. Each extra hop = one extra anchor in Cypher; one more CTE in SQL. |

The takeaway: **the shape of a real question rarely stays in one
column.** Walking edges, multi-hop traversal, paths-as-data, and
confidence-aware algorithms are where the graph form delivers what a
SQL engine plus three external services would deliver, in one query.

## Run

```bash
uv sync
uv run python 01-shared-coworkers.py
uv run python 02-confidence-tiered-query.py
uv run python 03-multi-hop-industry.py
```

`_common.py` is the shared fixture — 10 persons, 6 orgs, 25 employment
edges, identical content loaded into both engines so the answers
match cell-for-cell.

## Capabilities exercised

| Capability | What it does for the SQL migrator |
|---|---|
| WorldCypher graph traversal (`MATCH (a)-[r]->(b)`) | Replaces multi-self-join SQL with one pattern; hop depth becomes one character |
| First-class relationships with properties on edges | New relationship types are a label, not a table-shape migration |
| `_confidence` on every node and edge | `WHERE confidence > 0.85` and confidence-aware algorithms read the same column |
| PostgreSQL wire-protocol compatibility | Existing SQL tooling (`psql`, DBeaver, `sqlx`) connects directly — no toolchain rebuild |

## Rust SDK alongside

The `rust/` subfolder ships the same three comparisons via the Rust
SDK + the `duckdb` Rust crate, demonstrating how a single Rust process
can hold both connections (graph + SQL) for hybrid workloads where
each engine handles the queries it wins on.

## See also

- [`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/) — three patterns where the difference is most stark (counterfactual replay, confidence-weighted ER, observed-vs-predicted fusion)
- [`temporal-counterfactual-replay`](../temporal-counterfactual-replay/) — focused `AS OF seq` replay across fraud, robotics, IoT
- [`fraud-graph-traversal`](../fraud-graph-traversal/) — fan-out / fan-in / chain detection as Cypher patterns (with the equivalent Cypher mapping)
