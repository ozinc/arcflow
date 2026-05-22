"""
Question 1: "Who has worked at the same company as Alice?"

This is the simplest graph traversal — and it's the question that
shows the SQL-to-graph translation cost most clearly. In SQL, you
self-join the employment table. In Cypher, you walk the edge.
"""

from _common import make_duckdb, make_arcflow

print("=" * 68)
print("Q1: Who has worked at the same company as Alice?")
print("=" * 68)

# ──────────────────────── DuckDB / SQL ────────────────────────
print("\n--- DuckDB / SQL ---")
sql = """
SELECT DISTINCT p2.name, o.name AS org
FROM persons p1
JOIN employment e1 ON p1.id = e1.person_id
JOIN orgs o ON e1.org_id = o.id
JOIN employment e2 ON o.id = e2.org_id
JOIN persons p2 ON e2.person_id = p2.id
WHERE p1.name = 'Alice' AND p2.name <> 'Alice'
ORDER BY p2.name, o.name
"""
print(sql.strip())
print("\nresult:")
db = make_duckdb()
for r in db.execute(sql).fetchall():
    print(f"  {r}")
db.close()

# ──────────────────────── ArcFlow / Cypher ────────────────────────
print("\n--- ArcFlow / Cypher ---")
cypher = """
MATCH (alice:Person {name: 'Alice'})-[:EMPLOYED_AT]->(o:Org)<-[:EMPLOYED_AT]-(other:Person)
WHERE other.name <> 'Alice'
RETURN DISTINCT other.name AS name, o.name AS org
ORDER BY name, org
"""
print(cypher.strip())
print("\nresult:")
af = make_arcflow()
for r in af.execute(cypher):
    print(f"  ({r['name']!r}, {r['org']!r})")
af.close()

print("\n--- Observation ---")
print("SQL needs FOUR joins to walk the same edge twice. Cypher walks it once.")
print("Both produce the same result, but as the path length grows, SQL's")
print("self-join chain grows quadratically; Cypher stays one MATCH per hop.")
