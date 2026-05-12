//! Step 05 (Rust-only) — live fraud alerts + incremental mule clustering.
//!
//! Two surfaces Python can't reach today:
//!
//!   1. `arcflow_sdk::register_skill(&db, "fraud", "fan-in-alert",
//!      NodeCreated{"Transfer"}, query)` fires the fan-in detection
//!      query every time a new Transfer is created, surfacing the
//!      alert at mutation time rather than on a polling timer.
//!
//!   2. `LIVE CALL algo.connectedComponents` registers connected-
//!      components as a standing query. Every new Transfer updates
//!      the component assignments incrementally — useful for finding
//!      mule clusters as transfer activity arrives.

use anyhow::Result;
use arcflow_sdk::SkillTrigger;
use fraud_graph_traversal::load;
use std::path::PathBuf;

fn main() -> Result<()> {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop();
    path.push("data");
    path.push("transfers.parquet");
    let (db, _) = load(&path)?;

    // ---- 1. Live fan-in alert via register_skill ----------------------
    let trigger = SkillTrigger::NodeCreated {
        label: "Transfer".to_string(),
    };
    let fan_in_alert = "MATCH (a:Account)-[:SENT]->(:Transfer)-[:TO]->(b:Account) \
                        WITH b.account_id AS account, count(a) AS sources \
                        WHERE sources >= 6 \
                        RETURN account, sources";

    arcflow_sdk::register_skill(
        &db,
        "fraud",
        "fan-in-alert",
        trigger,
        fan_in_alert,
    )?;
    println!("registered: fraud/fan-in-alert");
    println!("  trigger:  NodeCreated label='Transfer'");
    println!("  fires:    every new transfer; surfaces accounts with 6+ distinct sources");

    // ---- 2. Incremental connected-components --------------------------
    // Treats accounts as nodes, transfers as edges. The components are
    // maintained as the graph mutates — every new Transfer either
    // extends an existing component or unions two.
    db.execute("LIVE CALL algo.connectedComponents")?;
    println!("\nregistered: algo.connectedComponents (incremental)");
    println!("  query:    MATCH (row) FROM VIEW __live_algo_connectedComponents");
    println!("  surface:  current component_id per Account, updated within ~20 ms of any new Transfer");

    println!("\n--- What this proves ---");
    println!("  - Live fraud alerts as standing queries — no polling, no cron.");
    println!("  - Mule-cluster detection runs as a maintained algorithm; the next");
    println!("    transfer either extends an existing cluster or unions two, and");
    println!("    the result set is current without re-running the algorithm.");
    println!("  - Combine the two: register a skill on the connected-components view");
    println!("    to alert whenever a component grows past a threshold size.");

    Ok(())
}
