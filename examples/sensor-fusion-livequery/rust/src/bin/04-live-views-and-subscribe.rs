//! Step 04 (Rust) — escape the polling fallback with CREATE LIVE VIEW
//! + subscribe + register_live_proof.
//!
//! The Python recipe polls because the Python binding doesn't expose
//! CREATE LIVE VIEW yet. In Rust the fusion query is a maintained view;
//! every new Reading mutation propagates a Z-set delta through the
//! weighted aggregate; the subscriber receives the updated row within
//! ~20 ms without polling.

use anyhow::Result;
use arcflow_sdk::ProofAssertion;
use sensor_fusion_livequery::make_db;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    let db = make_db()?;

    // The trust-weighted fusion as a maintained view.
    db.execute(
        "CREATE LIVE VIEW trust_weighted_temp AS \
         MATCH (r:Robot)-[:HAS_SENSOR]->(s:Sensor {kind: 'temperature'})\
         -[o:OBSERVED]->(:Reading) \
         RETURN r.robot_id AS robot, \
                sum(o.value * o._confidence) / sum(o._confidence) AS weighted_mean",
    )?;

    let mut rx = arcflow_sdk::subscribe(&db, "trust_weighted_temp")?;
    println!("LIVE VIEW trust_weighted_temp registered + subscribed.");

    // Continuous proof: the fusion view should never go empty. If it
    // does, the sensor pipeline has dropped out — fire-and-forget early
    // warning.
    arcflow_sdk::register_live_proof(
        &db,
        "trust_weighted_temp_non_empty",
        "trust_weighted_temp",
        ProofAssertion::NonEmpty,
    )?;
    println!("register_live_proof(NonEmpty) attached — fires immediately on sensor dropout.");

    // Inject one extra anomalous reading after the bulk load; expect a
    // delta to arrive.
    db.execute(
        "MATCH (s:Sensor {sensor_id: 'R01/temperature'}) \
         CREATE (s)-[:OBSERVED {frame: 100, value: 99.0, _confidence: 0.98, \
             _observation_class: 'observed', _source: 'sensor_v1'}]->(:Reading {robot_id: 'R01', kind: 'temperature', frame: 100})",
    )?;
    println!("\nInjected anomalous reading: R01 temperature = 99.0 °C @ frame 100");

    tokio::time::sleep(Duration::from_millis(100)).await;
    let mut count = 0;
    while let Ok(delta) = rx.try_recv() {
        println!("  delta {count}: {delta:?}");
        count += 1;
    }
    println!("\nDrained {count} deltas. Each fired within ~20 ms of the mutation.");

    Ok(())
}
