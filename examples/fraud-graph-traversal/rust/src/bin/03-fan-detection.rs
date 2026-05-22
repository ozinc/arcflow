//! Step 03 (Rust) — fan-out / fan-in detection.
//!
//! Mirrors `03-fan-detection.py`. Two single-MATCH queries, no
//! self-joins. The planted `SPLITTER-1` (fan-out, 9 recipients) and
//! `MULE-1` (fan-in, 12 sources) surface deterministically.

use anyhow::Result;
use fraud_graph_traversal::load;
use std::path::PathBuf;

const FAN_THRESHOLD: i64 = 6;

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("data");
    path.push("transfers.parquet");
    let (db, _) = load(&path)?;

    // ---- Fan-out: one source, many distinct recipients ----------------
    println!("[fan-out] Accounts sending to >= {FAN_THRESHOLD} distinct recipients:");
    let q1 = format!(
        "MATCH (a:Account)-[:SENT]->(:Transfer)-[:TO]->(b:Account) \
         RETURN a.account_id AS account, count(b) AS distinct_recipients \
         ORDER BY distinct_recipients DESC \
         LIMIT 10"
    );
    for row in db.execute(&q1)?.rows {
        let n: i64 = row.get("distinct_recipients")
            .and_then(|s| s.parse().ok()).unwrap_or(0);
        if n < FAN_THRESHOLD {
            continue;
        }
        println!("  {} → {n} recipients",
            row.get("account").cloned().unwrap_or_default());
    }

    // ---- Fan-in: one beneficiary, many distinct sources ----------------
    println!("\n[fan-in] Accounts receiving from >= {FAN_THRESHOLD} distinct sources:");
    let q2 = format!(
        "MATCH (a:Account)-[:SENT]->(:Transfer)-[:TO]->(b:Account) \
         RETURN b.account_id AS account, count(a) AS distinct_sources \
         ORDER BY distinct_sources DESC \
         LIMIT 10"
    );
    for row in db.execute(&q2)?.rows {
        let n: i64 = row.get("distinct_sources")
            .and_then(|s| s.parse().ok()).unwrap_or(0);
        if n < FAN_THRESHOLD {
            continue;
        }
        println!("  {} ← {n} sources",
            row.get("account").cloned().unwrap_or_default());
    }
    Ok(())
}
