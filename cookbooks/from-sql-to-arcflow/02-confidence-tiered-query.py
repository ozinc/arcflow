"""
Question 2: "Show employment relationships, but only the high-confidence ones."

In SQL, confidence is a column on a join table — you filter by it like any
other predicate. In ArcFlow, confidence is a first-class property on the
edge with semantic meaning the engine knows about (algorithms can weight
by it, standing queries can fire on threshold crossings, etc.).

This recipe shows the basic mechanics; the deeper value (confidence-
weighted PageRank, drift detection, calibrated retrieval) is in the
spatiotemporal-tactical-queries cookbook.
"""

from _common import make_duckdb, make_arcflow

print("=" * 68)
print("Q2: High-confidence employment relationships only (confidence > 0.85)")
print("=" * 68)

# ──────────────────────── DuckDB / SQL ────────────────────────
print("\n--- DuckDB / SQL ---")
sql = """
SELECT p.name AS person, o.name AS org, e.confidence
FROM persons p
JOIN employment e ON p.id = e.person_id
JOIN orgs o ON o.id = e.org_id
WHERE e.confidence > 0.85
ORDER BY e.confidence DESC
LIMIT 5
"""
print(sql.strip())
print("\nresult:")
db = make_duckdb()
for r in db.execute(sql).fetchall():
    print(f"  person={r[0]!r:>10} org={r[1]!r:>12} conf={r[2]:.2f}")
db.close()

# ──────────────────────── ArcFlow / Cypher ────────────────────────
print("\n--- ArcFlow / Cypher ---")
cypher = """
MATCH (p:Person)-[e:EMPLOYED_AT]->(o:Org)
WHERE e.confidence > 0.85
RETURN p.name AS person, o.name AS org, e.confidence AS conf
ORDER BY conf DESC
LIMIT 5
"""
print(cypher.strip())
print("\nresult:")
af = make_arcflow()
for r in af.execute(cypher):
    print(f"  person={r['person']!r:>10} org={r['org']!r:>12} conf={float(r['conf']):.2f}")
af.close()

print("\n--- Observation ---")
print("Same shape — both are simple filtered projections. The difference is")
print("downstream: ArcFlow algorithms (algo.confidencePageRank,")
print("algo.confidencePath) consume `_confidence` natively. SQL has no native")
print("graph-algorithmic primitive that knows about confidence.")
