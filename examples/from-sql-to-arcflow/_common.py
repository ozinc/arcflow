"""Shared synthesized fixture: load identical data into both DuckDB and ArcFlow.

The data shape is deliberately small so each side-by-side comparison runs in
under a second — what matters is the QUERY shape, not the data volume.

Fixture:
- 10 Persons (id, name, role)
- 6 Organizations (id, name, industry)
- 25 EMPLOYED_AT edges (person_id, org_id, since_year, confidence)
"""

from arcflow import ArcFlow
import duckdb

PERSONS = [
    (1, "Alice",   "engineer"),
    (2, "Bob",     "engineer"),
    (3, "Carol",   "manager"),
    (4, "Dave",    "engineer"),
    (5, "Eve",     "designer"),
    (6, "Frank",   "manager"),
    (7, "Grace",   "engineer"),
    (8, "Heidi",   "designer"),
    (9, "Ivan",    "manager"),
    (10, "Judy",   "engineer"),
]

ORGS = [
    (101, "Acme",    "tech"),
    (102, "BetaCo",  "tech"),
    (103, "GammaDx", "biotech"),
    (104, "DeltaIO", "fintech"),
    (105, "EpsilonX","tech"),
    (106, "ZetaLab", "biotech"),
]

# (person_id, org_id, since_year, confidence)
EMPLOYMENT = [
    (1, 101, 2018, 0.95),
    (1, 102, 2020, 0.92),
    (2, 102, 2019, 0.94),
    (3, 101, 2017, 0.98),
    (4, 103, 2021, 0.65),  # low confidence
    (4, 105, 2022, 0.88),
    (5, 102, 2020, 0.91),
    (5, 105, 2023, 0.96),
    (6, 104, 2019, 0.99),
    (7, 103, 2021, 0.55),  # low confidence
    (7, 106, 2022, 0.93),
    (8, 102, 2020, 0.94),
    (9, 104, 2018, 0.97),
    (9, 105, 2021, 0.83),
    (10, 101, 2019, 0.92),
    (10, 102, 2021, 0.88),
    (1, 105, 2023, 0.40),  # very low confidence
    (2, 105, 2023, 0.45),
    (3, 105, 2024, 0.93),
    (5, 106, 2024, 0.78),
    (6, 106, 2023, 0.94),
    (7, 105, 2024, 0.80),
    (8, 105, 2024, 0.86),
    (9, 106, 2024, 0.91),
    (10, 105, 2024, 0.75),
]


def make_duckdb():
    db = duckdb.connect(":memory:")
    db.execute("CREATE TABLE persons (id INT, name VARCHAR, role VARCHAR)")
    db.execute("CREATE TABLE orgs (id INT, name VARCHAR, industry VARCHAR)")
    db.execute("CREATE TABLE employment (person_id INT, org_id INT, since_year INT, confidence DOUBLE)")
    db.executemany("INSERT INTO persons VALUES (?, ?, ?)", PERSONS)
    db.executemany("INSERT INTO orgs VALUES (?, ?, ?)", ORGS)
    db.executemany("INSERT INTO employment VALUES (?, ?, ?, ?)", EMPLOYMENT)
    return db


def make_arcflow():
    db = ArcFlow()
    # Use execute() + integer literals for ids — keeps things straightforward.
    for pid, name, role in PERSONS:
        db.execute(
            f"CREATE (p:Person {{id: {pid}, name: '{name}', role: '{role}'}})"
        )
    for oid, name, industry in ORGS:
        db.execute(
            f"CREATE (o:Org {{id: {oid}, name: '{name}', industry: '{industry}'}})"
        )
    for pid, oid, year, conf in EMPLOYMENT:
        db.execute(
            f"MATCH (p:Person {{id: {pid}}}), (o:Org {{id: {oid}}}) "
            f"CREATE (p)-[:EMPLOYED_AT {{since_year: {year}, confidence: {conf}}}]->(o)"
        )
    return db
