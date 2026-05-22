//! Step 02 (Rust) — load the sensor stream and verify shape.

use anyhow::Result;
use sensor_fusion_livequery::make_db;

fn main() -> Result<()> {
    let db = make_db()?;
    for (label, q) in [
        ("Robots",     "MATCH (r:Robot)    RETURN count(*) AS n"),
        ("Sensors",    "MATCH (s:Sensor)   RETURN count(*) AS n"),
        ("Readings",   "MATCH (r:Reading)  RETURN count(*) AS n"),
        ("Observations", "MATCH ()-[o:OBSERVED]->() RETURN count(*) AS n"),
    ] {
        let result = db.execute(q)?;
        let n = result.rows.first().and_then(|r| r.get("n")).cloned().unwrap_or_else(|| "0".to_string());
        println!("  {label:<14} {n}");
    }
    Ok(())
}
