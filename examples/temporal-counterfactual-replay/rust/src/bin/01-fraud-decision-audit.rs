//! Step 01 (Rust) — fraud decision audit via AS OF seq.
//!
//! A customer's risk score evolves over a short timeline. A transfer
//! is approved at seq N reading the risk-score visible at that
//! moment. Later the risk-score is updated. The auditor asks: "what
//! score was visible at decision time?"

use anyhow::Result;

fn main() -> Result<()> {
    let db = arcflow_sdk::open_concurrent();

    // seq 1: create the customer with initial risk_score
    db.execute(
        "CREATE (:Customer {customer_id: 'C-001', risk_score: 0.21, \
            _observation_class: 'observed', _confidence: 1.0, \
            _source: 'underwriting_v1'})",
    )?;
    println!("seq 1: customer C-001 created with risk_score=0.21");

    // seq 2: record the transfer decision (uses risk_score visible at seq 1)
    db.execute(
        "CREATE (:Transfer {transfer_id: 'T-9381', customer_id: 'C-001', \
            amount: 12500, decision: 'APPROVED', \
            _observation_class: 'observed', _confidence: 1.0, \
            _source: 'fraud_engine_v1'})",
    )?;
    println!("seq 2: transfer T-9381 APPROVED");

    // seq 3: risk score updated (e.g. new pattern recognition fires)
    db.execute(
        "MATCH (c:Customer {customer_id: 'C-001'}) SET c.risk_score = 0.82",
    )?;
    println!("seq 3: risk_score updated to 0.82 (post-decision)");

    // The audit query: same MATCH, AS OF different seqs
    println!("\n--- Audit: what was risk_score at decision time? ---");
    for seq in [1u64, 2, 3] {
        let q = format!(
            "MATCH (c:Customer {{customer_id: 'C-001'}}) \
             AS OF seq {seq} \
             RETURN c.risk_score AS risk"
        );
        for row in db.execute(&q)?.rows {
            println!("  AS OF seq {seq}: risk_score = {}",
                row.get("risk").cloned().unwrap_or_default());
        }
    }

    println!("\n--- Verdict ---");
    println!("  At seq 2 (decision time): risk_score = 0.21 — APPROVAL justified.");
    println!("  The update at seq 3 is post-decision; using it would be look-ahead.");

    Ok(())
}
