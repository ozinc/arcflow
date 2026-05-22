//! Step 04 (Rust) — tracking bulk-load and shape verification.
//!
//! Mirrors `04-tracking-bulk-load.py`. Builds the canonical Session +
//! Frame + Entity + OBSERVED_AT shape, then prints counts to confirm
//! the substrate is queryable.

use anyhow::Result;
use multi_stream_spatiotemporal_world_model::make_db;

fn main() -> Result<()> {
    let db = make_db()?;
    println!("Substrate loaded:");
    for (label, q) in [
        ("sessions",     "MATCH (s:Session)               RETURN count(*) AS n"),
        ("frames",       "MATCH (f:Frame)                 RETURN count(*) AS n"),
        ("entities",     "MATCH (e:Entity)                RETURN count(*) AS n"),
        ("observations", "MATCH ()-[r:OBSERVED_AT]->()    RETURN count(*) AS n"),
    ] {
        let result = db.execute(q)?;
        let n = result.rows.first()
            .and_then(|r| r.get("n")).cloned()
            .unwrap_or_else(|| "0".to_string());
        println!("  {label:12} {n}");
    }
    Ok(())
}
