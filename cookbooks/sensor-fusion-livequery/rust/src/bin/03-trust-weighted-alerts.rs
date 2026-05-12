//! Step 03 (Rust) — trust-weighted alerts.
//!
//! The fusion query: per-robot weighted mean of temperature, where the
//! weight is the per-reading _confidence. The alert predicate is one
//! WHERE clause on the weighted average.

use anyhow::Result;
use sensor_fusion_livequery::make_db;

const ALERT_THRESHOLD: f64 = 28.0; // degrees C

fn main() -> Result<()> {
    let db = make_db()?;

    println!("=== Trust-weighted temperature mean per robot ===");
    // sum(value * conf) / sum(conf) — one RETURN expression
    let q = format!(
        "MATCH (r:Robot)-[:HAS_SENSOR]->(s:Sensor {{kind: 'temperature'}})\
         -[o:OBSERVED]->(:Reading) \
         RETURN r.robot_id AS robot, \
                sum(o.value * o._confidence) / sum(o._confidence) AS weighted_mean, \
                count(o) AS n_readings \
         ORDER BY robot"
    );
    for row in db.execute(&q)?.rows {
        let robot = row.get("robot").cloned().unwrap_or_default();
        let mean: f64 = row.get("weighted_mean").and_then(|s| s.parse().ok()).unwrap_or(0.0);
        let n: u32 = row.get("n_readings").and_then(|s| s.parse().ok()).unwrap_or(0);
        let flag = if mean > ALERT_THRESHOLD { " 🚨 ALERT" } else { "" };
        println!("  {robot}: weighted_mean = {mean:.2} °C (n={n}){flag}");
    }
    println!("\nAlert threshold: {ALERT_THRESHOLD} °C");

    Ok(())
}
