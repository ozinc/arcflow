"""
Question 3: "Find every person within 2 hops of Alice (via shared employers)
who has worked in biotech."

This is the question SQL handles worst: the path itself is the data, not
just the endpoints. SQL needs to enumerate intermediate nodes via repeated
self-joins; the depth is hardcoded in the SQL. Cypher walks the path.

Real-world version: "show me every analyst within 2 reporting hops of the
fraud incident" / "show me every codebase symbol within 3 import hops of
the changed file" — same shape, different domain.
"""

from _common import make_duckdb, make_arcflow

print("=" * 68)
print("Q3: People within 2 employment-hops of Alice who've worked in biotech")
print("=" * 68)

# ──────────────────────── DuckDB / SQL ────────────────────────
print("\n--- DuckDB / SQL ---")
sql = """
WITH alice AS (
    SELECT id FROM persons WHERE name = 'Alice'
),
alice_orgs AS (                          -- hop 1: Alice's orgs
    SELECT e.org_id FROM employment e JOIN alice ON e.person_id = alice.id
),
hop1_people AS (                         -- people who shared an org with Alice
    SELECT DISTINCT e.person_id
    FROM employment e
    JOIN alice_orgs ao ON e.org_id = ao.org_id
    WHERE NOT e.person_id = (SELECT id FROM alice)
),
hop2_orgs AS (                           -- hop 2: orgs of those people
    SELECT DISTINCT e.org_id
    FROM employment e
    JOIN hop1_people hp ON e.person_id = hp.person_id
)
SELECT DISTINCT p.name, o.name AS via_org
FROM employment e
JOIN persons p ON p.id = e.person_id
JOIN orgs o ON o.id = e.org_id
WHERE e.org_id IN (SELECT org_id FROM hop2_orgs)
  AND o.industry = 'biotech'
  AND p.id <> (SELECT id FROM alice)
ORDER BY p.name
"""
print(sql.strip())
print("\nresult:")
db = make_duckdb()
for r in db.execute(sql).fetchall():
    print(f"  {r[0]!r:>10} via {r[1]!r}")
db.close()

# ──────────────────────── ArcFlow / Cypher ────────────────────────
# arcflow-core#13 (lexer) resolved 2026-05-05 (oz-arcflow >= 1.6.9): `!=`
# is now an alias for `<>`. NOT x = y is kept here only because the
# multi-anchor predicates below trip the still-open arcflow-core#10 +
# arcflow-core#14 planner bugs.
# FIXME(arcflow-core#14): inline {industry: 'biotech'} on terminal anchor
#   is silently ignored on multi-hop patterns. The natural form should be:
#     ...->(p:Person)-[:EMPLOYED_AT]->(o2:Org {industry: 'biotech'})
# FIXME(arcflow-core#10): WHERE clause combining multi-anchor predicates
#   returns 0 rows. So the natural WHERE form also fails:
#     WHERE NOT p.name = 'Alice' AND o2.industry = 'biotech'
# Until both ship, the working pattern is: pull all hops, filter in app.
print("\n--- ArcFlow / Cypher (with Python post-filter) ---")
cypher = """
MATCH (alice:Person {name: 'Alice'})-[:EMPLOYED_AT]->(o1:Org)<-[:EMPLOYED_AT]-(p:Person)-[:EMPLOYED_AT]->(o2:Org)
WHERE NOT p.name = 'Alice'
RETURN DISTINCT p.name AS name, o2.name AS via_org, o2.industry AS industry
ORDER BY name
"""
print(cypher.strip())
print("\nresult (biotech-filtered in Python until #10/#14 ship):")
af = make_arcflow()
results = [r for r in af.execute(cypher) if r["industry"] == "biotech"]
for r in results:
    print(f"  {r['name']!r:>10} via {r['via_org']!r}")
af.close()

print("\n--- Observation ---")
print("SQL: 5 CTEs, 4 joins, hardcoded path depth. To extend to 3 hops, add")
print("hop3_orgs and another join chain. Each hop multiplies the join count.")
print("")
print("Cypher: one MATCH that walks the path. To extend to 3 hops, add")
print("`(p)-[:EMPLOYED_AT]->(o3:Org)` and one more variable. The graph engine")
print("plans the traversal; you don't write the join order.")
