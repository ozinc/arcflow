//! Step 02 (Rust) — confidence-tiered query, both engines.
//!
//! Mirrors `02-confidence-tiered-query.py`. The flat filter is similar
//! in both engines; the lift is that ArcFlow's confidence column is
//! also consumed natively by confidence-aware algorithms
//! (algo.confidencePageRank, algo.confidencePath) when the question
//! needs propagation through joins.

use anyhow::Result;
use from_sql_to_arcflow::load_both;

const MIN_CONF: f64 = 0.85;

fn main() -> Result<()> {
    let both = load_both()?;

    println!("=== Employment relationships with confidence >= {MIN_CONF} ===\n");

    println!("--- SQL (DuckDB) ---");
    let sql_q = format!(
        "SELECT p.name AS person, o.name AS org, e.confidence \
         FROM employment e \
         JOIN persons p ON p.id = e.person_id \
         JOIN orgs o ON o.id = e.org_id \
         WHERE e.confidence >= {MIN_CONF} \
         ORDER BY e.confidence DESC",
    );
    println!("{sql_q}");
    let mut stmt = both.sql.prepare(&sql_q)?;
    let rows: Vec<(String, String, f64)> = stmt
        .query_map([], |row| Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, f64>(2)?,
        )))?
        .filter_map(|r| r.ok())
        .collect();
    for (person, org, conf) in &rows {
        println!("  {person:>8} @ {org:<12} conf={conf:.2}");
    }
    println!();

    println!("--- WorldCypher (ArcFlow) ---");
    let cy = format!(
        "MATCH (p:Person)-[r:WORKED_AT]->(o:Org) \
         WHERE r.confidence >= {MIN_CONF} \
         RETURN p.name AS person, o.name AS org, r.confidence AS confidence \
         ORDER BY r.confidence DESC"
    );
    println!("{cy}");
    let result = both.graph.execute(&cy)?;
    for row in &result.rows {
        println!(
            "  {:>8} @ {:<12} conf={}",
            row.get("person").cloned().unwrap_or_default(),
            row.get("org").cloned().unwrap_or_default(),
            row.get("confidence").cloned().unwrap_or_default(),
        );
    }

    println!("\nVerdict: same shape in both engines for the flat filter.");
    println!("Lift in ArcFlow: the same confidence column powers algo.confidencePageRank,");
    println!("algo.confidencePath, and live-proof assertions — no application-layer plumbing.");
    Ok(())
}
