"""
IoT trigger replay — why did the alarm fire?

Pattern: a smart-building alarm fires. Operations needs to know what
sensor readings triggered it — and at the same time, what the OTHER
sensors in the building looked like at that exact moment, to disambiguate
between "real fire" and "calibration drift on one sensor".

`AS OF seq <param>` reads the multi-sensor world state at the alarm seq.

Setup: three sensors report readings over time. One sensor's reading
crosses an alarm threshold. The replay queries every sensor's reading
at the alarm seq.
"""

import shutil
import tempfile

from arcflow import ArcFlow

def main():
    data_dir = tempfile.mkdtemp(prefix="arcflow-iot-replay-")
    db = ArcFlow(data_dir)

    # Seqs 1-3: three sensors report initial readings.
    db.execute("CREATE (s:Sensor {id: 'temp-A1', value: 22.0, kind: 'temp'})")
    db.execute("CREATE (s:Sensor {id: 'temp-A2', value: 22.5, kind: 'temp'})")
    db.execute("CREATE (s:Sensor {id: 'smoke-B', value: 0.02, kind: 'smoke'})")
    print("seqs 1-3: baseline readings — temp-A1=22.0, temp-A2=22.5, smoke-B=0.02")

    # Seqs 4-6: temp-A1 starts drifting. Temp-A2 stable. Smoke flat.
    db.execute("MATCH (s:Sensor {id: 'temp-A1'}) SET s.value = 41.0")
    db.execute("MATCH (s:Sensor {id: 'temp-A2'}) SET s.value = 22.7")
    db.execute("MATCH (s:Sensor {id: 'smoke-B'}) SET s.value = 0.03")
    print("seqs 4-6: temp-A1 jumps to 41.0; temp-A2 still 22.7; smoke-B 0.03")

    # Seq 7: ALARM FIRES — temp-A1 crossed the 40°C threshold.
    db.execute("""
        CREATE (a:Alarm {
            id: 'alarm-001',
            triggered_by: 'temp-A1',
            reason: 'temperature_threshold_exceeded'
        })
    """)
    alarm_seq = 7
    print(f"seq {alarm_seq}: ALARM FIRED on temp-A1 threshold breach")

    # Seqs 8-9: more readings come in after the alarm.
    db.execute("MATCH (s:Sensor {id: 'temp-A1'}) SET s.value = 22.1")  # back to normal
    db.execute("MATCH (s:Sensor {id: 'temp-A2'}) SET s.value = 22.6")
    print("seqs 8-9: post-alarm — temp-A1 drops back to 22.1 (calibration drift?)")

    # The triage question: at the alarm moment, what did EVERY sensor say?
    print(f"\nAS OF seq {alarm_seq} — full sensor state at alarm-fire moment:")
    for r in db.execute(
        "MATCH (s:Sensor) AS OF seq $s "
        "RETURN s.id AS id, s.kind AS kind, s.value AS value "
        "ORDER BY id",
        params={"s": alarm_seq},
    ):
        print(f"  {dict(r)}")

    print("\nObservation: at alarm time, temp-A1 read 41.0°C but temp-A2 (same")
    print("zone) read 22.7°C and smoke-B was flat at 0.03. Strong evidence the")
    print("alarm was triggered by a single-sensor anomaly, not a real event.")
    print("Without temporal replay, ops would only see the post-alarm state where")
    print("temp-A1 is back to normal — looking like the alarm was a phantom.")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
