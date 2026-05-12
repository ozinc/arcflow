//! Shared fixture for the Sensor Fusion Rust SDK example.
//!
//! 3 robots × 2 sensors (temperature, vibration) × 100 timesteps = 600
//! Reading nodes. Sensor 2 on R02 is deliberately noisier (mean
//! confidence 0.55 vs 0.92). A temperature anomaly is planted at
//! frames 60–70 on R01 so the trust-weighted alert fires.

use anyhow::Result;
use arcflow_sdk::ConcurrentStore;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;

pub const ROBOTS: &[&str] = &["R01", "R02", "R03"];
pub const SENSORS: &[(&str, f64)] = &[
    // (kind, baseline_confidence_mean)
    ("temperature", 0.92),
    ("vibration",   0.85),
];
pub const TIMESTEPS: u32 = 100;
pub const ANOMALY_ROBOT: &str = "R01";
pub const ANOMALY_FRAMES: std::ops::Range<u32> = 60..70;

pub fn make_db() -> Result<ConcurrentStore> {
    let mut rng = ChaCha8Rng::seed_from_u64(13);
    let db = arcflow_sdk::open_concurrent();

    for robot in ROBOTS {
        db.execute(&format!(
            "CREATE (:Robot {{robot_id: '{robot}', \
                _observation_class: 'observed', _confidence: 1.0, \
                _source: 'fleet_registry_v1'}})"
        ))?;
        for (kind, _) in SENSORS {
            let sensor_id = format!("{robot}/{kind}");
            db.execute(&format!(
                "MATCH (r:Robot {{robot_id: '{robot}'}}) \
                 CREATE (r)-[:HAS_SENSOR]->(:Sensor {{ \
                    sensor_id: '{sensor_id}', kind: '{kind}', \
                    _observation_class: 'observed', _confidence: 1.0, \
                    _source: 'fleet_registry_v1' \
                 }})"
            ))?;
        }
    }

    for frame in 0..TIMESTEPS {
        for robot in ROBOTS {
            for (kind, base_conf) in SENSORS {
                let sensor_id = format!("{robot}/{kind}");

                let conf = if *robot == "R02" && *kind == "vibration" {
                    rng.gen_range(0.35..0.70)
                } else {
                    rng.gen_range(base_conf - 0.05..(base_conf + 0.05).min(1.0))
                };

                let mut value: f64 = match *kind {
                    "temperature" => rng.gen_range(22.0..26.0),
                    "vibration"   => rng.gen_range(0.10..0.40),
                    _ => 0.0,
                };
                if *robot == ANOMALY_ROBOT
                    && *kind == "temperature"
                    && ANOMALY_FRAMES.contains(&frame)
                {
                    value += 12.0; // planted spike
                }

                db.execute(&format!(
                    "MATCH (s:Sensor {{sensor_id: '{sensor_id}'}}) \
                     CREATE (s)-[:OBSERVED {{ \
                        frame: {frame}, value: {value:.3}, \
                        _confidence: {conf:.3}, \
                        _observation_class: 'observed', _source: 'sensor_v1' \
                     }}]->(:Reading {{robot_id: '{robot}', kind: '{kind}', frame: {frame}}})"
                ))?;
            }
        }
    }

    Ok(db)
}
