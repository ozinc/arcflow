"""Shared loader used by every step that needs the graph in memory.

Each step opens a fresh in-memory ArcFlow database and re-loads from the
Parquet file. For 600 rows this is well under one second — faster than
persisting and re-opening on a fresh process.

Schema (see 01-schema-design.md for the rationale):
    (:Robot {robot_id})
    (:Sensor {sensor_id, robot_id, modality}) -[:MOUNTED_ON]-> (:Robot)
    (:Frame  {frame_id, timestamp})
    (:Sensor)-[:READ {value, confidence}]->(:Frame)

Each (Sensor, Frame) pair is unique — one edge per reading.
"""
from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from arcflow import ArcFlow

HERE = Path(__file__).parent
INPUT = HERE / "data" / "stream.parquet"


def load(verbose: bool = False, max_frame: int | None = None):
    """Load stream.parquet into a fresh in-memory ArcFlow.

    Returns (db, rows). If max_frame is set, only loads readings with
    frame_id <= max_frame — used by the live-polling step to simulate
    progressive arrival.
    """
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT}. Run 00-make-sample.py first.")

    table = pq.read_table(INPUT)
    rows = table.to_pylist()
    if max_frame is not None:
        rows = [r for r in rows if r["frame_id"] <= max_frame]

    robots = sorted({r["robot_id"] for r in rows})
    sensors = sorted({(r["sensor_id"], r["modality"], r["robot_id"]) for r in rows})
    frames = sorted({(r["frame_id"], r["timestamp"]) for r in rows})

    db = ArcFlow()

    for rid in robots:
        db.execute(f"CREATE (:Robot {{robot_id: '{rid}'}})")

    for sid, modality, rid in sensors:
        db.execute(
            "CREATE (:Sensor {"
            f"sensor_id: '{sid}', robot_id: '{rid}', modality: '{modality}'"
            "})"
        )
        db.execute(
            "MATCH (s:Sensor {sensor_id: '" + sid + "'}), "
            "(b:Robot {robot_id: '" + rid + "'}) "
            "CREATE (s)-[:MOUNTED_ON]->(b)"
        )

    for frame_id, ts in frames:
        db.execute(
            "CREATE (:Frame {"
            f"frame_id: {frame_id}, timestamp: {ts}"
            "})"
        )

    for r in rows:
        db.execute(
            "MATCH (s:Sensor {sensor_id: '" + r["sensor_id"] + "'}), "
            f"(f:Frame {{frame_id: {r['frame_id']}}}) "
            "CREATE (s)-[:READ {"
            f"value: {r['value']}, confidence: {r['confidence']}"
            "}]->(f)"
        )

    if verbose:
        print(
            f"loaded {len(rows)} readings, {len(robots)} robots, "
            f"{len(sensors)} sensors, {len(frames)} frames"
        )

    return db, rows
