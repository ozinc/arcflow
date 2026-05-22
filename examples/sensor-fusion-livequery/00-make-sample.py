"""Synthesize the sensor stream Parquet file used by subsequent steps.

Three robots, two sensor modalities each (temperature in °C, vibration in
mm/s). 100 frames at 10Hz. Reading-level confidence varies per sensor — the
"flaky" sensor (R02/vibration) hovers near 0.55, the well-calibrated ones
near 0.92. One temperature anomaly is planted on R01 between frame 60 and
70 to drive the alert in step 04.

Output:
    data/stream.parquet  (~25 KB)

Schema:
    timestamp     float64    seconds
    frame_id      int64
    robot_id      str
    sensor_id     str
    modality      str        "temperature" | "vibration"
    value         float64    measurement
    confidence    float64    [0, 1] sensor self-reported reliability

Deterministic — same seed → byte-equal output, so CI snapshots stay stable.
"""
from __future__ import annotations

import random
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def main() -> None:
    rng = random.Random(20260430)
    out = Path(__file__).parent / "data" / "stream.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)

    robots = ["R01", "R02", "R03"]
    modalities = ["temperature", "vibration"]
    n_frames = 100
    dt = 0.1

    # Per-(robot, modality) baseline + confidence band.
    baseline = {
        ("R01", "temperature"): (45.0, 0.92),
        ("R01", "vibration"): (1.5, 0.92),
        ("R02", "temperature"): (45.0, 0.92),
        ("R02", "vibration"): (1.5, 0.55),   # flaky sensor
        ("R03", "temperature"): (45.0, 0.92),
        ("R03", "vibration"): (1.5, 0.92),
    }

    rows = {
        "timestamp": [],
        "frame_id": [],
        "robot_id": [],
        "sensor_id": [],
        "modality": [],
        "value": [],
        "confidence": [],
    }

    for frame_id in range(n_frames):
        t = frame_id * dt
        for robot in robots:
            for modality in modalities:
                base, conf_mean = baseline[(robot, modality)]
                value = rng.gauss(base, 0.5 if modality == "temperature" else 0.2)
                # Planted anomaly: R01 temperature spikes to ~75°C between
                # frames 60 and 70. The trust-weighted alert must fire here.
                if robot == "R01" and modality == "temperature" and 60 <= frame_id <= 70:
                    value = rng.gauss(75.0, 1.0)
                confidence = max(0.0, min(1.0, rng.gauss(conf_mean, 0.05)))

                sensor_id = f"{robot}-{modality[:4].upper()}"
                rows["timestamp"].append(round(t, 4))
                rows["frame_id"].append(frame_id)
                rows["robot_id"].append(robot)
                rows["sensor_id"].append(sensor_id)
                rows["modality"].append(modality)
                rows["value"].append(round(value, 4))
                rows["confidence"].append(round(confidence, 4))

    table = pa.table(
        rows,
        schema=pa.schema(
            [
                ("timestamp", pa.float64()),
                ("frame_id", pa.int64()),
                ("robot_id", pa.string()),
                ("sensor_id", pa.string()),
                ("modality", pa.string()),
                ("value", pa.float64()),
                ("confidence", pa.float64()),
            ]
        ),
    )

    pq.write_table(table, out, compression="snappy")
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out} ({len(rows['timestamp'])} rows, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
