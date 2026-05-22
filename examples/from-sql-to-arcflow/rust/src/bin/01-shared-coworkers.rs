//! Step 01 (Rust) — shared coworkers, both engines side-by-side.
//!
//! Mirrors `01-shared-coworkers.py`. The graph form walks one edge;
//! the SQL form needs four self-joins.

use anyhow::Result;
use from_sql_to_arcflow::load_both;

fn main() -> Result<()> {
    let both = load_both()?;

    println!("=== Shared coworkers of Alice ===\n");

    println!("--- SQL (DuckDB) ---");
    let sql_q = "
        SELECT DISTINCT p2.name AS coworker
        FROM employment e1
        JOIN persons p1 ON p1.id = e1.person_id
        JOIN employment e2 ON e2.org_id = e1.org_id
        JOIN persons p2 ON p2.id = e2.person_id
        WHERE p1.name = 'Alice' AND p2.name != 'Alice'
        ORDER BY p2.name
    ";
    let mut stmt = both.sql.prepare(sql_q)?;
    let rows: Vec<String> = stmt
        .query_map([], |row| row.get::<_, String>(0))?
        .filter_map(|r| r.ok())
        .collect();
    println!("{}", sql_q.trim());
    println!("→ {rows:?}\n");

    println!("--- WorldCypher (ArcFlow) ---");
    let cy = "MATCH (p1:Person {name: 'Alice'})-[:WORKED_AT]->(o:Org)<-[:WORKED_AT]-(p2:Person) \
              WHERE p2.name <> 'Alice' \
              RETURN DISTINCT p2.name AS coworker \
              ORDER BY coworker";
    println!("{cy}");
    let result = both.graph.execute(cy)?;
    let names: Vec<String> = result.rows.into_iter()
        .filter_map(|r| r.get("coworker").cloned())
        .collect();
    println!("→ {names:?}\n");

    println!("Verdict: Cypher walks one edge; SQL needs four self-joins.");
    Ok(())
}
