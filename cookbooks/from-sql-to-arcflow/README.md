# From SQL to ArcFlow

**What you'll build:** Three side-by-side comparisons of the same question
answered in DuckDB SQL and ArcFlow WorldCypher. Same data, same answer,
different shape — designed to give a SQL user a fast, honest sense of
what changes (and what doesn't) in the move.

**Audience:** python, data-engineer, sql-user.

**Runtime:** under 1 minute total.

**ArcFlow version:** 1.6.7. **DuckDB:** 1.0+.

## Why this recipe

Most engineers evaluating a graph database have a SQL background and a
working DuckDB / Postgres / SQLite muscle memory. The legitimate
question is: **for the queries my application actually runs, is the
graph form better, worse, or about the same?**

Three questions chosen for the side-by-side, each from a different
gradient on that scale:

| Recipe | Question | Verdict |
|---|---|---|
| `01-shared-coworkers.py` | "Who has worked at the same company as Alice?" | Cypher walks one edge; SQL needs four self-joins. Same answer, much shorter Cypher. |
| `02-confidence-tiered-query.py` | "Show employment relationships with confidence > 0.85" | Identical shape — both are simple filtered projections. Cypher's win is downstream (algorithms consume `_confidence` natively). |
| `03-multi-hop-industry.py` | "People within 2 hops of Alice who've worked in biotech" | SQL: 5 CTEs and a hardcoded path depth. Cypher: one MATCH chain. Each extra hop is one extra anchor in Cypher; one more CTE in SQL. |

The takeaway isn't "Cypher is always better" — for a flat filtered
projection (recipe 02), they're identical. The takeaway is: **the
shapes that hurt SQL most are the shapes graphs handle natively.**
Walking edges, multi-hop traversal, paths-as-data, and confidence-aware
algorithms are where you stop fighting the model.

## Run

```bash
uv sync
uv run python 01-shared-coworkers.py
uv run python 02-confidence-tiered-query.py
uv run python 03-multi-hop-industry.py
```

`_common.py` is the shared fixture — 10 persons, 6 orgs, 25 employment
edges, identical content loaded into both engines.

## Engine quirks observed during authoring (1.6.7)

Filed engine-side; tagged inline in the recipe code with `FIXME(arcflow-core#NNN)`.

| Issue | Quirk | Recipe affected |
|---|---|---|
| [#10](https://github.com/ozinc/arcflow-core/issues/10) | WHERE chains over multi-anchor patterns can return 0 rows. | 03 |
| [#13](https://github.com/ozinc/arcflow-core/issues/13) | `<>` returns 0 rows silently; `!=` errors. Workaround: `NOT x = y`. | 01, 03 |
| [#14](https://github.com/ozinc/arcflow-core/issues/14) | Inline property predicate on a multi-hop pattern's terminal anchor is silently ignored. | 03 |

The recipes use the working workarounds; once the engine fixes ship,
grep for `FIXME(arcflow-core#` to find the spots that can be cleaned up.

## See Also

- [`spatiotemporal-tactical-queries`](../spatiotemporal-tactical-queries/) — three patterns where the difference is most stark (counterfactual replay, confidence-weighted ER, observed-vs-predicted fusion).
- [`temporal-counterfactual-replay`](../temporal-counterfactual-replay/) — focused AS OF replay across fraud / robotics / IoT.
- [PostgreSQL Wire Protocol](/sql-to-gql) — connect SQL clients (psql, DBeaver, sqlx) directly to ArcFlow over the PG wire protocol; another migration on-ramp.
