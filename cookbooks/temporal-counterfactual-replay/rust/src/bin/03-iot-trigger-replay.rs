//! Step 03 (Rust) — IoT alarm triage via AS OF seq.
//!
//! Multiple sensors. One fires an alarm. The reviewer needs to know
//! what the OTHER sensors said at that same moment — to distinguish a
//! real event from a calibration drift.

use anyhow::Result;

fn main() -> Result<()> {
    let db = arcflow_sdk::open_concurrent();

    // Initial state: three sensors with readings
    db.execute("CREATE (:Sensor {id: 'temp-A', reading: 22.0, \
        _observation_class: 'observed', _confidence: 0.95, _source: 'iot_v1'})")?;
    db.execute("CREATE (:Sensor {id: 'temp-B', reading: 22.1, \
        _observation_class: 'observed', _confidence: 0.93, _source: 'iot_v1'})")?;
    db.execute("CREATE (:Sensor {id: 'smoke',  reading: 0.02, \
        _observation_class: 'observed', _confidence: 0.88, _source: 'iot_v1'})")?;
    println!("seqs 1-3: three sensors initialised");

    // seq 4: temp-A spikes
    db.execute("MATCH (s:Sensor {id: 'temp-A'}) SET s.reading = 47.5")?;
    println!("seq 4: temp-A reading jumps to 47.5 °C");

    // seq 5: alarm fires
    db.execute("CREATE (:Alarm {id: 'AL-001', kind: 'OVERTEMP', \
        triggered_by_sensor: 'temp-A', \
        _observation_class: 'observed', _confidence: 1.0, _source: 'iot_v1'})")?;
    println!("seq 5: alarm AL-001 (OVERTEMP) fired");

    // seq 6: temp-A returns to normal (it was a calibration spike)
    db.execute("MATCH (s:Sensor {id: 'temp-A'}) SET s.reading = 22.2")?;
    println!("seq 6: temp-A returns to 22.2 °C (spike was transient)");

    // Replay: at alarm fire time, what did the OTHER sensors say?
    println!("\n--- Triage: cross-sensor reading at alarm fire time (seq 5) ---");
    for sid in ["temp-A", "temp-B", "smoke"] {
        let q = format!(
            "MATCH (s:Sensor {{id: '{sid}'}}) \
             AS OF seq 5 \
             RETURN s.id AS id, s.reading AS reading, s._confidence AS conf"
        );
        for row in db.execute(&q)?.rows {
            println!("  {row:?}");
        }
    }

    println!("\n  At alarm time: temp-A = 47.5 (spike), temp-B = 22.1 (normal), smoke = 0.02 (normal).");
    println!("  Cross-sensor disagreement → likely calibration drift on temp-A, not a real fire.");
    println!("  Subsequent return to normal at seq 6 confirms the calibration-drift hypothesis.");

    Ok(())
}
