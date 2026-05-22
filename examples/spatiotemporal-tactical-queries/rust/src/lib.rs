//! Shared fixture for the Spatiotemporal Tactical Queries Rust SDK example.
//!
//! 22 entities (alpha + beta groups), 60 frames at 60 Hz, two tracking
//! sources with planted disagreement on a subset, multi-namespace
//! identifiers with deliberate gaps and a collision, and a small set of
//! predicted facts on a future frame for the calibration analysis.

use anyhow::Result;
use arcflow_sdk::ConcurrentStore;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;

pub const FRAMES: u32 = 60;
pub const ENTITIES_PER_GROUP: u32 = 11;
pub const FUTURE_PREDICTION_FRAME: u32 = 80;

pub fn make_db() -> Result<ConcurrentStore> {
    let mut rng = ChaCha8Rng::seed_from_u64(17);
    let db = arcflow_sdk::open_concurrent();

    // Alpha + Beta entities, each with multi-namespace identifiers.
    for group in ["alpha", "beta"] {
        for i in 0..ENTITIES_PER_GROUP {
            let entity_id = format!("{group}-{i:02}");
            let id_a = format!("A-{group}-{i:02}");
            let id_b = format!("B-{group}-{i:02}");
            // Deliberate gap: every 5th entity is missing id_c.
            let id_c = if i % 5 == 0 {
                "null".to_string()
            } else {
                format!("'C-{group}-{i:02}'")
            };
            db.execute(&format!(
                "CREATE (:Entity {{entity_id: '{entity_id}', group: '{group}', \
                    id_a: '{id_a}', id_b: '{id_b}', id_c: {id_c}, \
                    _observation_class: 'observed', _confidence: 1.0, \
                    _source: 'roster_v1'}})"
            ))?;
        }
    }

    // Identity collision: alpha-00 and beta-00 share an id_a (the kind of
    // mistake cross-source ER catches).
    db.execute(
        "MATCH (e:Entity {entity_id: 'beta-00'}) SET e.id_a = 'A-alpha-00'",
    )?;

    // Frames + observations from two tracking sources.
    for frame in 0..FRAMES {
        db.execute(&format!(
            "CREATE (:Frame {{frame_idx: {frame}, time_master_ns: {ns}, \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'master_clock_v1'}})",
            ns = (frame as i64) * 16_666_667,
        ))?;
    }

    for group in ["alpha", "beta"] {
        for i in 0..ENTITIES_PER_GROUP {
            let entity_id = format!("{group}-{i:02}");
            for frame in 0..FRAMES {
                let x_true = (i as f64) * 5.0 + (frame as f64) * 0.1;
                let y_true = (frame as f64) * 0.05;

                // Source A: always present, high confidence
                let x_a = x_true + rng.gen_range(-0.1..0.1);
                let y_a = y_true + rng.gen_range(-0.1..0.1);
                db.execute(&format!(
                    "MATCH (e:Entity {{entity_id: '{entity_id}'}}), \
                           (f:Frame {{frame_idx: {frame}}}) \
                     CREATE (e)-[:OBSERVED_AT {{ \
                        x: {x_a:.2}, y: {y_a:.2}, source: 'A', \
                        _confidence: 0.95, _observation_class: 'observed', \
                        _source: 'tracker_A' \
                     }}]->(f)"
                ))?;

                // Source B: occasionally disagrees (planted disagreement on group=alpha, even frames)
                let (x_b, y_b, conf_b) = if group == "alpha" && frame % 6 == 0 {
                    (x_true + 4.0, y_true + 4.0, 0.62) // disagreement
                } else {
                    (x_true + rng.gen_range(-0.2..0.2), y_true + rng.gen_range(-0.2..0.2), 0.82)
                };
                db.execute(&format!(
                    "MATCH (e:Entity {{entity_id: '{entity_id}'}}), \
                           (f:Frame {{frame_idx: {frame}}}) \
                     CREATE (e)-[:OBSERVED_AT {{ \
                        x: {x_b:.2}, y: {y_b:.2}, source: 'B', \
                        _confidence: {conf_b}, _observation_class: 'observed', \
                        _source: 'tracker_B' \
                     }}]->(f)"
                ))?;
            }
        }
    }

    // Predicted facts on a future frame (for calibration analysis).
    db.execute(&format!(
        "CREATE (:Frame {{frame_idx: {FUTURE_PREDICTION_FRAME}, \
            time_master_ns: {ns}, _observation_class: 'observed', _confidence: 1.0, \
            _source: 'master_clock_v1'}})",
        ns = (FUTURE_PREDICTION_FRAME as i64) * 16_666_667,
    ))?;
    for i in 0..ENTITIES_PER_GROUP {
        let entity_id = format!("alpha-{i:02}");
        let x_pred = (i as f64) * 5.0 + (FUTURE_PREDICTION_FRAME as f64) * 0.1;
        let y_pred = (FUTURE_PREDICTION_FRAME as f64) * 0.05;
        db.execute(&format!(
            "MATCH (e:Entity {{entity_id: '{entity_id}'}}), \
                   (f:Frame {{frame_idx: {FUTURE_PREDICTION_FRAME}}}) \
             CREATE (e)-[:PREDICTED_AT {{ \
                x: {x_pred:.2}, y: {y_pred:.2}, \
                _confidence: 0.55, _observation_class: 'predicted', \
                _source: 'trajectory_model_v1' \
             }}]->(f)"
        ))?;
    }

    Ok(db)
}
