//! Shared substrate for the Multi-Stream Spatiotemporal World Model
//! Rust SDK example.
//!
//! Builds a small canonical timeline: a Session, N Frames at 60 Hz, K
//! Entities, OBSERVED_AT edges from each Entity to each Frame with the
//! spatial coordinates and confidence on the edge property. The Python
//! recipe scales this to ~20K observations over 30 s × 22 entities;
//! the Rust example keeps numbers smaller for fast cargo runs.

use anyhow::Result;
use arcflow_sdk::ConcurrentStore;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;

pub const FRAMES: u32 = 60;          // 1 second at 60 Hz
pub const ENTITIES: u32 = 22;
pub const SESSION_ID: &str = "session-rust-01";

pub fn make_db() -> Result<ConcurrentStore> {
    let mut rng = ChaCha8Rng::seed_from_u64(11);
    let db = arcflow_sdk::open_concurrent();

    // Session + Frames (canonical 60 Hz timeline)
    db.execute(&format!(
        "CREATE (:Session {{session_id: '{SESSION_ID}', \
            coordinate_frame: 'session-local', tick_hz: 60, \
            _observation_class: 'observed', _confidence: 1.0, \
            _source: 'recipe_rust_v1'}})"
    ))?;

    for f in 0..FRAMES {
        let t_master_ns = (f as i64) * 16_666_667;
        db.execute(&format!(
            "MATCH (s:Session {{session_id: '{SESSION_ID}'}}) \
             CREATE (s)-[:TICKED_AT]->(:Frame {{ \
                frame_idx: {f}, time_master_ns: {t_master_ns}, \
                coordinate_frame: 'session-local', \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'tracker_v1' \
             }})"
        ))?;
    }

    // Entities + OBSERVED_AT edges with x/y on the edge, dqi → _confidence
    for e in 0..ENTITIES {
        let entity_id = format!("alpha-{e:02}");
        let team = if e < ENTITIES / 2 { "blue" } else { "red" };
        db.execute(&format!(
            "CREATE (:Entity {{entity_id: '{entity_id}', team: '{team}', \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'roster_v1'}})"
        ))?;

        for f in 0..FRAMES {
            let x: f64 = rng.gen_range(0.0..120.0);
            let y: f64 = rng.gen_range(0.0..80.0);
            let dqi: f64 = rng.gen_range(0.85..1.0);
            let obs_class = if dqi >= 0.95 { "observed" } else { "inferred" };
            db.execute(&format!(
                "MATCH (e:Entity {{entity_id: '{entity_id}'}}), \
                       (f:Frame {{frame_idx: {f}}}) \
                 CREATE (e)-[:OBSERVED_AT {{ \
                    x: {x:.2}, y: {y:.2}, \
                    _observation_class: '{obs_class}', _confidence: {dqi:.3}, \
                    _source: 'tracker_v1' \
                 }}]->(f)"
            ))?;
        }
    }

    Ok(db)
}
