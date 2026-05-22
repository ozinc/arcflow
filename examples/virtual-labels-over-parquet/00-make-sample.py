"""Step 00 — Synthesize a small Hive-partitioned Parquet tree.

Writes a 5-day × 4-sensor synthetic telemetry stream into
`data/lake/telemetry/year=2026/month=03/day=DD/sensor=SS.parquet`.
Each file holds 240 per-minute samples (one per minute for 4 hours).

The shape mimics what you would see from a real telemetry pipeline —
date-partitioned at the top, sensor-partitioned underneath, columnar
inside. It is the canonical input for `01-register.py`.

Run:
    uv run python 00-make-sample.py
"""
from __future__ import annotations

import math
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


LAKE_ROOT = Path("data/lake")
TABLE = "telemetry"
DAYS = ["14", "15", "16", "17", "18"]    # 2026-03-14 .. 2026-03-18
SENSORS = ["s01", "s02", "s03", "s04"]
SAMPLES_PER_DAY = 240                       # one per minute, 4 hours


def synth(day: str, sensor: str) -> pa.Table:
    """One day × one sensor → one Parquet table.

    Deterministic: same inputs always produce identical bytes so the
    fixture can be committed and the cookbook is reproducible.
    """
    base = datetime(2026, 3, int(day), 8, 0, 0, tzinfo=timezone.utc)
    rows = []
    for i in range(SAMPLES_PER_DAY):
        ts = base + timedelta(minutes=i)
        sensor_id = sensor
        temp = 20.0 + 5.0 * math.sin(i / 30.0) + (int(day) - 16) * 0.5
        humidity = 45.0 + 10.0 * math.cos(i / 47.0)
        rows.append((ts, sensor_id, temp, humidity))

    return pa.table(
        {
            "ts":         pa.array([r[0] for r in rows], type=pa.timestamp("us", tz="UTC")),
            "sensor_id":  pa.array([r[1] for r in rows], type=pa.string()),
            "temp_c":     pa.array([r[2] for r in rows], type=pa.float64()),
            "humidity":   pa.array([r[3] for r in rows], type=pa.float64()),
        }
    )


def main() -> None:
    t0 = time.perf_counter()
    if LAKE_ROOT.exists():
        shutil.rmtree(LAKE_ROOT)

    files_written = 0
    for day in DAYS:
        for sensor in SENSORS:
            out = LAKE_ROOT / TABLE / "year=2026" / "month=03" / f"day={day}" / f"sensor={sensor}.parquet"
            out.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(synth(day, sensor), out, compression="zstd")
            files_written += 1

    elapsed = time.perf_counter() - t0
    total_rows = files_written * SAMPLES_PER_DAY
    print(f"wrote {files_written} parquet files ({total_rows} rows total) in {elapsed:.2f}s")
    print(f"tree: {LAKE_ROOT}/{TABLE}/year=YYYY/month=MM/day=DD/sensor=SS.parquet")


if __name__ == "__main__":
    main()
