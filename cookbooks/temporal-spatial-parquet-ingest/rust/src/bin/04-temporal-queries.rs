//! Step 04 (Rust) — per-entity windowed temporal queries.

use anyhow::Result;
use std::path::PathBuf;
use temporal_spatial_parquet_ingest::load_both;

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("data");
    path.push("sample.parquet");
    let (graph, _) = load_both(&path)?;

    println!("=== Per-entity displacement (lag over frame) ===");
    let q = "MATCH (e:Entity)-[r:OBSERVED_AT]->(:Frame) \
             RETURN e.entity_id AS id, r.frame AS frame, r.x AS x, r.y AS y, \
                    r.x - lag(r.x, 1) OVER (PARTITION BY e.entity_id ORDER BY r.frame) AS dx, \
                    r.y - lag(r.y, 1) OVER (PARTITION BY e.entity_id ORDER BY r.frame) AS dy \
             ORDER BY id, frame LIMIT 10";
    for row in graph.execute(q)?.rows {
        println!("  {row:?}");
    }

    println!("\n=== Per-entity trajectory length (sum of per-frame deltas) ===");
    // Compute via two queries in Python or in one window pass — keep it simple here.
    let q = "MATCH (e:Entity)-[r:OBSERVED_AT]->(:Frame) \
             RETURN e.entity_id AS id, count(r) AS frames, \
                    min(r.frame) AS first, max(r.frame) AS last \
             ORDER BY id";
    for row in graph.execute(q)?.rows {
        println!("  {row:?}");
    }
    Ok(())
}
