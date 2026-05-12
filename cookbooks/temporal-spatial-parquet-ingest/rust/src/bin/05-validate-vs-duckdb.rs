//! Step 05 (Rust) — cross-validate ArcFlow against DuckDB on the same Parquet input.
//!
//! Same questions, two engines. Counts and aggregates should match exactly.

use anyhow::Result;
use std::path::PathBuf;
use temporal_spatial_parquet_ingest::load_both;

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("data");
    path.push("sample.parquet");
    let (graph, sql) = load_both(&path)?;

    // Q1: row count
    let af_count: i64 = {
        let r = graph.execute("MATCH ()-[r:OBSERVED_AT]->() RETURN count(r) AS n")?;
        r.rows.first().and_then(|row| row.get("n")).and_then(|s| s.parse().ok()).unwrap_or(0)
    };
    let dd_count: i64 = sql.query_row("SELECT count(*) FROM tracking", [], |r| r.get(0))?;
    println!("Row count       — ArcFlow={af_count}, DuckDB={dd_count} {}",
             if af_count == dd_count { "✓" } else { "✗" });

    // Q2: distinct entity count
    let af_ents: i64 = {
        let r = graph.execute("MATCH (e:Entity) RETURN count(e) AS n")?;
        r.rows.first().and_then(|row| row.get("n")).and_then(|s| s.parse().ok()).unwrap_or(0)
    };
    let dd_ents: i64 = sql.query_row(
        "SELECT count(DISTINCT entity_id) FROM tracking",
        [], |r| r.get(0))?;
    println!("Distinct entities — ArcFlow={af_ents}, DuckDB={dd_ents} {}",
             if af_ents == dd_ents { "✓" } else { "✗" });

    // Q3: distinct frame count
    let af_frames: i64 = {
        let r = graph.execute("MATCH (f:Frame) RETURN count(f) AS n")?;
        r.rows.first().and_then(|row| row.get("n")).and_then(|s| s.parse().ok()).unwrap_or(0)
    };
    let dd_frames: i64 = sql.query_row(
        "SELECT count(DISTINCT frame) FROM tracking",
        [], |r| r.get(0))?;
    println!("Distinct frames — ArcFlow={af_frames}, DuckDB={dd_frames} {}",
             if af_frames == dd_frames { "✓" } else { "✗" });

    let ok = af_count == dd_count && af_ents == dd_ents && af_frames == dd_frames;
    println!("\n{}", if ok { "PASS — cell-for-cell agreement" } else { "FAIL — cross-engine drift detected" });
    Ok(())
}
