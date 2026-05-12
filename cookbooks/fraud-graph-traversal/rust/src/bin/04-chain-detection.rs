//! Step 04 (Rust) — multi-hop layering chain detection.
//!
//! Mirrors `04-chain-detection.py`. A 4-hop `A → B → C → D` pattern where
//! each leg moves a similar amount surfaces by one MATCH with three
//! amount-similarity predicates. The planted `LAYER-A → LAYER-B → LAYER-C →
//! LAYER-D` chain at $9,500 ± noise surfaces deterministically.

use anyhow::Result;
use fraud_graph_traversal::load;
use std::path::PathBuf;

const CHAIN_AMOUNT_TOLERANCE: f64 = 1000.0; // dollars

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("data");
    path.push("transfers.parquet");
    let (db, _) = load(&path)?;

    // ---- 4-hop layering chain with similar amounts at each leg --------
    println!("[chain] 4-hop A → B → C → D with each leg within ${} of the next:",
             CHAIN_AMOUNT_TOLERANCE);
    let q = format!(
        "MATCH (a:Account)-[:SENT]->(t1:Transfer)-[:TO]->(b:Account)-[:SENT]->\
         (t2:Transfer)-[:TO]->(c:Account)-[:SENT]->\
         (t3:Transfer)-[:TO]->(d:Account) \
         WHERE abs(t1.amount - t2.amount) < {tol} \
           AND abs(t2.amount - t3.amount) < {tol} \
         RETURN a.account_id AS a, b.account_id AS b, \
                c.account_id AS c, d.account_id AS d, \
                t1.amount AS leg1, t2.amount AS leg2, t3.amount AS leg3 \
         LIMIT 20",
        tol = CHAIN_AMOUNT_TOLERANCE,
    );
    for row in db.execute(&q)?.rows {
        println!(
            "  {} → {} → {} → {}  (legs: ${} → ${} → ${})",
            row.get("a").cloned().unwrap_or_default(),
            row.get("b").cloned().unwrap_or_default(),
            row.get("c").cloned().unwrap_or_default(),
            row.get("d").cloned().unwrap_or_default(),
            row.get("leg1").cloned().unwrap_or_default(),
            row.get("leg2").cloned().unwrap_or_default(),
            row.get("leg3").cloned().unwrap_or_default(),
        );
    }
    Ok(())
}
