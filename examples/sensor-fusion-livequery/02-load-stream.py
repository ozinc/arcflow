"""Step 02 — Load data/stream.parquet into ArcFlow.

Reads the synthesized sensor stream and emits Robot, Sensor, Frame,
MOUNTED_ON, and READ nodes/edges. Reports the engine version it is
talking to so the recipe can be reproduced against a known build.

Run:
    uv run python 02-load-stream.py
"""
from __future__ import annotations

import time

from _load import load
from arcflow import ArcFlow


def main() -> None:
    print(f"engine version: {ArcFlow().version()}")

    t0 = time.perf_counter()
    db, rows = load(verbose=True)
    elapsed = time.perf_counter() - t0
    print(f"loaded in {elapsed:.2f}s ({len(rows) / elapsed:.0f} rows/sec)")

    n_robots = db.execute("MATCH (b:Robot) RETURN count(b)").get(0, 0)
    n_sensors = db.execute("MATCH (s:Sensor) RETURN count(s)").get(0, 0)
    n_frames = db.execute("MATCH (f:Frame) RETURN count(f)").get(0, 0)
    n_reads = db.execute("MATCH ()-[r:READ]->() RETURN count(r)").get(0, 0)

    print(
        f"in-graph: robots={n_robots}, sensors={n_sensors}, "
        f"frames={n_frames}, readings={n_reads}"
    )
    db.close()
    print("OK")


if __name__ == "__main__":
    main()
