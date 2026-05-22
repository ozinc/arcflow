//! Step 02 (Rust) — Parquet load into ArcFlow + sanity counts.

use anyhow::Result;
use std::path::PathBuf;
use temporal_spatial_parquet_ingest::load_both;

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("data");
    path.push("sample.parquet");

    let (graph, _sql) = load_both(&path)?;
    println!("Parquet loaded into ArcFlow graph and DuckDB table.");

    for (label, q) in [
        ("Entities", "MATCH (e:Entity) RETURN count(*) AS n"),
        ("Frames",   "MATCH (f:Frame)  RETURN count(*) AS n"),
        ("Observations", "MATCH ()-[r:OBSERVED_AT]->() RETURN count(*) AS n"),
    ] {
        let result = graph.execute(q)?;
        let n = result.rows.first().and_then(|r| r.get("n")).cloned().unwrap_or_else(|| "0".to_string());
        println!("  {label:<14} {n}");
    }
    Ok(())
}
