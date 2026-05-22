//! Step 03 (Rust) — multi-hop industry traversal, both engines.
//!
//! Mirrors `03-multi-hop-industry.py`. The graph form walks two hops
//! in one MATCH; the SQL form needs five CTEs and a hard-coded depth.

use anyhow::Result;
use from_sql_to_arcflow::load_both;

fn main() -> Result<()> {
    let both = load_both()?;

    println!("=== People within 2 hops of Alice who've worked in biotech ===\n");

    println!("--- SQL (DuckDB) — 5 CTEs, hard-coded depth ---");
    let sql_q = "
        WITH alice AS (
            SELECT id FROM persons WHERE name = 'Alice'
        ),
        alice_orgs AS (
            SELECT DISTINCT e.org_id FROM employment e, alice
            WHERE e.person_id = alice.id
        ),
        coworkers AS (
            SELECT DISTINCT e.person_id FROM employment e, alice_orgs
            WHERE e.org_id = alice_orgs.org_id
        ),
        coworker_orgs AS (
            SELECT DISTINCT e.org_id FROM employment e, coworkers
            WHERE e.person_id = coworkers.person_id
        ),
        biotech_orgs AS (
            SELECT id FROM orgs WHERE industry = 'biotech'
        )
        SELECT DISTINCT p.name
        FROM employment e
        JOIN persons p ON p.id = e.person_id
        JOIN coworker_orgs ON coworker_orgs.org_id = e.org_id
        JOIN biotech_orgs  ON biotech_orgs.id = e.org_id
        WHERE p.name != 'Alice'
        ORDER BY p.name
    ";
    println!("{}", sql_q.trim());
    let mut stmt = both.sql.prepare(sql_q)?;
    let rows: Vec<String> = stmt
        .query_map([], |row| row.get::<_, String>(0))?
        .filter_map(|r| r.ok())
        .collect();
    println!("→ {rows:?}\n");

    println!("--- WorldCypher (ArcFlow) — one MATCH chain ---");
    let cy = "MATCH (alice:Person {name: 'Alice'})-[:WORKED_AT]->(:Org)<-[:WORKED_AT]-\
              (coworker:Person)-[:WORKED_AT]->(o:Org {industry: 'biotech'}) \
              WHERE coworker.name <> 'Alice' \
              RETURN DISTINCT coworker.name AS name \
              ORDER BY name";
    println!("{cy}");
    let result = both.graph.execute(cy)?;
    let names: Vec<String> = result.rows.into_iter()
        .filter_map(|r| r.get("name").cloned())
        .collect();
    println!("→ {names:?}\n");

    println!("Verdict: each extra hop adds one anchor in Cypher; one more CTE in SQL.");
    Ok(())
}
