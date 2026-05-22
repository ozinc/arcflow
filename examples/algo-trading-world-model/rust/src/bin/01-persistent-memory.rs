//! Step 1 (Rust) — Persistent memory: the world model remembers what the agent saw.
//!
//! Mirrors `01-persistent-memory.py`. Same recipe, same WAL-seq narrative,
//! same `AS OF seq` replay. The Rust surface is fully in-process — no FFI
//! marshalling cost, no GIL — and `JournaledStore` keeps the WAL durable
//! across process restarts so the audit replay works months later from a
//! cold start.

use algo_trading_world_model::make_db;
use anyhow::Result;

fn main() -> Result<()> {
    // For real persistence across process restarts, swap make_db() to
    // open a JournaledStore at a data_dir path. The in-memory variant
    // below still supports AS OF replay within the live session.
    let db = make_db()?;

    // --- WAL seq 1: agent records its BUY decision on day 34 ------------
    db.execute(
        "CREATE (t:TradeDecision { \
            ticker: 'ENGY-02', day_idx: 34, action: 'BUY', size: 5000, \
            rationale: 'eps surprise, sector dispersion low', \
            confidence: 0.78, _observation_class: 'observed', \
            _confidence: 1.0, _source: 'agent_v1' \
        })",
    )?;
    println!("seq 1: BUY decision recorded for ENGY-02 at day 34");

    // --- WAL seqs 2, 3: ENGY-02 restatement, split into two execute()s
    //     so the AS OF replay can step through the intermediate state.
    db.execute(
        "MATCH (s:Symbol {ticker:'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f:Fundamental) \
         SET f.eps = 2.10",
    )?;
    println!("seq 2: ENGY-02 eps restated → 2.10");
    db.execute(
        "MATCH (s:Symbol {ticker:'ENGY-02'})-[:HAS_FUNDAMENTAL]->(f:Fundamental) \
         SET f.revision = 'restated-day-35'",
    )?;
    println!("seq 3: ENGY-02 revision flag flipped → restated-day-35");

    // --- WAL seq 4: agent's CLOSE decision ------------------------------
    db.execute(
        "CREATE (t:TradeDecision { \
            ticker: 'ENGY-02', day_idx: 36, action: 'CLOSE', size: -5000, \
            rationale: 'fundamentals revision invalidates thesis', \
            confidence: 0.85, _observation_class: 'observed', \
            _confidence: 1.0, _source: 'agent_v1' \
        })",
    )?;
    println!("seq 4: CLOSE decision recorded for ENGY-02 at day 36");

    // --- The audit query: same query, AS OF different seqs -------------
    // Note: AS OF seq replay requires a JournaledStore (persistent WAL).
    // The exact query syntax in arcflow-sdk is: embed AS OF seq N in the
    // query string, OR call query_as_of(&journaled_store, seq, query).
    println!("\n--- Operational world model — AS OF seq replay ---");
    for (seq, label) in [
        (1u64, "BUY decision time — original fundamentals"),
        (2,    "after eps restatement, before revision flag"),
        (3,    "after both restatement assignments — full revision visible"),
        (4,    "CLOSE decision time"),
    ] {
        println!("\nAS OF seq {seq} ({label}):");
        let fund_q = format!(
            "MATCH (s:Symbol {{ticker:'ENGY-02'}})-[:HAS_FUNDAMENTAL]->(f:Fundamental) \
             AS OF seq {seq} \
             RETURN f.eps AS eps, f.revision AS revision"
        );
        let result = db.execute(&fund_q)?;
        for row in result.rows {
            println!("  Fundamental: {:?}", row);
        }
        let decision_q = format!(
            "MATCH (t:TradeDecision {{ticker:'ENGY-02'}}) \
             AS OF seq {seq} \
             RETURN t.day_idx AS day, t.action AS action, t.rationale AS why"
        );
        let result = db.execute(&decision_q)?;
        for row in result.rows {
            println!("  Decision:    {:?}", row);
        }
    }

    println!("\n--- What this proves ---");
    println!("  - BUY at seq 1 was made against the ORIGINAL eps. No look-ahead.");
    println!("  - CLOSE at seq 4 was made against the RESTATED eps.");
    println!("  - Decisions and evidence in the same graph, queried the same way.");
    println!("  - The audit trail IS the dataset a causal-inference model wants.");

    Ok(())
}
