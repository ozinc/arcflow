//! Step 02 (Rust) — load the transfer fixture from Parquet.
//!
//! Mirrors `02-load.py`. Reads `../data/transfers.parquet` (generated
//! by `../00-make-sample.py`) and builds the Account/Transfer schema.

use anyhow::Result;
use fraud_graph_traversal::load;
use std::path::PathBuf;

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop(); // rust/ → cookbook root
    path.push("data");
    path.push("transfers.parquet");

    let (db, transfer_count) = load(&path)?;
    println!("loaded {transfer_count} transfers");

    for (label, q) in [
        ("Accounts",  "MATCH (a:Account)  RETURN count(*) AS n"),
        ("Transfers", "MATCH (t:Transfer) RETURN count(*) AS n"),
    ] {
        let result = db.execute(q)?;
        let n = result.rows.first()
            .and_then(|r| r.get("n"))
            .cloned()
            .unwrap_or_else(|| "0".to_string());
        println!("  {label:<10} {n}");
    }
    Ok(())
}
