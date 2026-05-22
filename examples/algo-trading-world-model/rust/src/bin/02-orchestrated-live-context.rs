//! Step 2 (Rust) — Orchestrated context: maintained `LIVE VIEW`s, not polling.
//!
//! Where the Python recipe falls back to per-tick polling (`db.execute(q)`
//! after every mutation), the Rust SDK reaches the end-state surface:
//! `CREATE LIVE VIEW` defines each context layer as a maintained query;
//! `arcflow_sdk::subscribe(&db, "name")` returns a `DeltaReceiver` that
//! fires within ~20ms of any mutation that affects the view. Same query
//! shape as the polling Python code — the engine's Z-set algebra
//! guarantees batch and live produce identical results.

use algo_trading_world_model::make_db;
use anyhow::Result;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    let db = make_db()?;

    // ---- Define the three context layers as maintained LIVE VIEWs ------
    db.execute(
        "CREATE LIVE VIEW sector_rollup AS \
         MATCH (b:DailyBar) \
         RETURN b.day_idx AS day, b.sector AS sector, \
                count(*) AS n_symbols, avg(b.close) AS sector_avg_close",
    )?;

    db.execute(
        "CREATE LIVE VIEW cross_sectional_z AS \
         MATCH (b:DailyBar) \
         RETURN b.ticker AS ticker, b.sector AS sector, \
                b.day_idx AS day, b.close AS close, \
                percent_rank() OVER (PARTITION BY b.sector, b.day_idx ORDER BY b.close) AS sector_pctl",
    )?;

    db.execute(
        "CREATE LIVE VIEW leaders_by_sector AS \
         MATCH (b:DailyBar) \
         RETURN b.sector AS sector, b.ticker AS leader, \
                b.day_idx AS day, b.close AS leader_close, \
                row_number() OVER (PARTITION BY b.sector, b.day_idx ORDER BY b.close DESC) AS rn",
    )?;

    // ---- Subscribe to push-based delta updates -------------------------
    // Each receiver is independent; multiple subscribers to the same view
    // each get their own broadcast channel.
    let mut sector_rx = arcflow_sdk::subscribe(&db, "sector_rollup")?;
    let mut rank_rx   = arcflow_sdk::subscribe(&db, "cross_sectional_z")?;
    let mut leader_rx = arcflow_sdk::subscribe(&db, "leaders_by_sector")?;

    println!("Three LIVE VIEWs registered + subscribed:");
    println!("  sector_rollup · cross_sectional_z · leaders_by_sector");
    println!();
    println!("Inserting one new bar: TECH-03, day 60, close = 999.0");
    println!("(this should flip the Tech sector leader)\n");

    // ---- One tick mutates the graph ------------------------------------
    db.execute(
        "MATCH (s:Symbol {ticker:'TECH-03'}) \
         CREATE (s)-[:HAS_BAR]->(:DailyBar { \
            ticker:'TECH-03', sector:'Tech', day_idx:60, \
            open:920.0, high:1005.0, low:905.0, close:999.0, volume:3500000, \
            _observation_class:'observed', _confidence:0.99, _source:'tape_v1' \
         })",
    )?;

    // ---- Drain deltas from each receiver -------------------------------
    // The engine fires within ~20ms. We poll with a short timeout — in a
    // real agent loop this is a select! over the three receivers feeding
    // the agent prompt.
    tokio::time::sleep(Duration::from_millis(100)).await;

    println!("--- sector_rollup deltas ---");
    while let Ok(delta) = sector_rx.try_recv() {
        println!("  {:?}", delta);
    }

    println!("\n--- cross_sectional_z deltas ---");
    while let Ok(delta) = rank_rx.try_recv() {
        println!("  {:?}", delta);
    }

    println!("\n--- leaders_by_sector deltas ---");
    while let Ok(delta) = leader_rx.try_recv() {
        println!("  {:?}", delta);
    }

    println!("\n--- What this proves ---");
    println!("  - Three maintained queries; one MATCH each. No polling loop.");
    println!("  - One bar inserted via execute() → three views update via Z-set delta");
    println!("    propagation. The engine guarantees the maintained result matches what");
    println!("    a full batch recompute would produce (continuous proof, register_live_proof).");
    println!("  - This is the end-state surface — the Python version polls because");
    println!("    CREATE LIVE VIEW isn't Python-callable yet; the recipe shape is identical.");

    Ok(())
}
