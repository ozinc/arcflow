//! Step 01 (Rust) — counterfactual replay via AS OF seq.
//!
//! Reads the world model state at past WAL sequence numbers. Same
//! query, different `AS OF seq` literal, bit-for-bit reconstructable
//! result.

use anyhow::Result;
use spatiotemporal_tactical_queries::make_db;

fn main() -> Result<()> {
    let db = make_db()?;

    println!("=== AS OF replay: alpha-00 position across early seqs ===");
    // Sample a few seqs to show the world model evolving.
    for seq in [50u64, 500, 1000, 2000] {
        let q = format!(
            "MATCH (e:Entity {{entity_id: 'alpha-00'}})-[r:OBSERVED_AT {{source: 'A'}}]->(f:Frame) \
             AS OF seq {seq} \
             RETURN f.frame_idx AS frame, r.x AS x, r.y AS y \
             ORDER BY f.frame_idx LIMIT 3"
        );
        println!("\n-- AS OF seq {seq} --");
        for row in db.execute(&q)?.rows {
            println!("  {row:?}");
        }
    }

    println!("\n--- What this proves ---");
    println!("  - Same MATCH, different AS OF seq → exact past-state reconstruction.");
    println!("  - No separate audit table. The WAL IS the audit table.");

    Ok(())
}
