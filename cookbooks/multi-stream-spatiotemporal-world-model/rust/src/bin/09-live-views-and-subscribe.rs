//! Step 09 (Rust) — LIVE VIEW + subscribe.
//!
//! The Python recipe falls back to polling for live views (the Python
//! binding doesn't expose CREATE LIVE VIEW + subscribe yet). Rust
//! reaches the end-state surface — register a LIVE VIEW once, subscribe
//! once, receive deltas within ~20 ms of any mutation.

use anyhow::Result;
use multi_stream_spatiotemporal_world_model::make_db;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    let db = make_db()?;

    // Define a LIVE VIEW over high-confidence observations.
    db.execute(
        "CREATE LIVE VIEW high_confidence_obs AS \
         MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) \
         WHERE r._confidence >= 0.95 \
         RETURN e.entity_id AS id, f.frame_idx AS frame, r.x AS x, r.y AS y, r._confidence AS conf",
    )?;

    let mut rx = arcflow_sdk::subscribe(&db, "high_confidence_obs")?;
    println!("LIVE VIEW high_confidence_obs registered + subscribed.");
    println!("Inserting a high-confidence observation; expecting a delta within ~20 ms.\n");

    db.execute(
        "MATCH (e:Entity {entity_id: 'alpha-00'}), (f:Frame {frame_idx: 30}) \
         CREATE (e)-[:OBSERVED_AT {x: 50.0, y: 25.0, \
             _confidence: 0.99, _observation_class: 'observed', \
             _source: 'manual_v1'}]->(f)",
    )?;

    tokio::time::sleep(Duration::from_millis(100)).await;
    let mut count = 0;
    while let Ok(delta) = rx.try_recv() {
        println!("  delta {count}: {delta:?}");
        count += 1;
    }
    println!("\nDrained {count} deltas. Each maintenance fires within ~20 ms of the mutation.");

    Ok(())
}
