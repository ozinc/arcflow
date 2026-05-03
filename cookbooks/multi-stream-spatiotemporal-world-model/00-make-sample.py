"""Synthesize the multi-stream sample dataset.

Generates four Parquet files in data/sample/:

  - tracking.parquet  — 60 Hz × 22 entities × 30 seconds = 39,600 rows
  - scenes.parquet    — 30 Hz × 30 seconds = 900 rows (scene-reconstruction refs)
  - imu.parquet       — 200 Hz × 30 seconds × 1 entity = 6,000 rows (biomechanical)
  - events.parquet    — sparse, ~30 events across the session
  - ground_truth.json — counts + aggregates the synthesizer knows by
                        construction; downstream validation cross-checks
                        ArcFlow's results against this ledger

Deterministic — seeded RNG produces byte-equal Parquet on every run.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


HERE = Path(__file__).parent
OUT = HERE / "data" / "sample"
SESSION_ID = "session-2026-05-01-a"

# Cadences
TRACK_HZ = 60
SCENE_HZ = 30
IMU_HZ = 200
DURATION_S = 15

# Entities
GROUPS = ["alpha", "beta"]              # two groups, 11 each + 1 free entity
ENTITIES_PER_GROUP = 11                  # ~team-sport / fleet shape
N_ENTITIES = ENTITIES_PER_GROUP * 2      # 22 tracked entities

# Field — generic spatial extents so the recipe doesn't pin a domain
FIELD_X = (0.0, 120.0)
FIELD_Y = (0.0, 80.0)


def synthesize_tracking(rng: random.Random) -> tuple[pa.Table, dict]:
    """60 Hz tracking. Each entity follows a randomly-seeded velocity field
    with mild per-frame noise. Returns the Arrow table and a ground-truth
    summary the validator can cross-check.
    """
    n_frames = TRACK_HZ * DURATION_S  # 1800

    rows: dict[str, list] = {
        "session_id": [],
        "entity_id": [],
        "group": [],
        "frame_idx": [],
        "time_master_ns": [],
        "x": [],
        "y": [],
        "speed": [],
        "accel": [],
        "heading_deg": [],
        "orient_deg": [],
        "dqi": [],   # data quality index 0..1
    }

    # Per-entity initial conditions
    state: dict[str, dict] = {}
    for g_idx, group in enumerate(GROUPS):
        for n in range(ENTITIES_PER_GROUP):
            entity_id = f"{group}-{n:02d}"
            x0 = (FIELD_X[1] / 2) + (-2.0 if g_idx == 0 else 2.0)
            y0 = 5.0 + n * (FIELD_Y[1] - 10.0) / ENTITIES_PER_GROUP
            vx = rng.gauss(2.0 if g_idx == 0 else -2.0, 1.5)
            vy = rng.gauss(0.0, 1.0)
            state[entity_id] = {
                "x0": x0, "y0": y0, "vx": vx, "vy": vy, "group": group,
            }

    dt = 1.0 / TRACK_HZ
    for frame_idx in range(n_frames):
        t_ns = frame_idx * (10**9 // TRACK_HZ)
        for entity_id, st in state.items():
            t = frame_idx * dt
            nx = rng.gauss(0.0, 0.05)
            ny = rng.gauss(0.0, 0.05)
            x = max(FIELD_X[0], min(FIELD_X[1], st["x0"] + st["vx"] * t + nx))
            y = max(FIELD_Y[0], min(FIELD_Y[1], st["y0"] + st["vy"] * t + ny))
            speed = math.hypot(st["vx"], st["vy"])
            accel = abs(rng.gauss(0.0, 0.5))
            heading = (math.degrees(math.atan2(st["vy"], st["vx"])) + 360) % 360
            orient = (heading + rng.gauss(0.0, 5.0)) % 360
            # Inject occasional bad-tracking frames so the confidence layer is exercised
            dqi = 0.30 if rng.random() < 0.005 else round(rng.uniform(0.92, 0.99), 4)

            rows["session_id"].append(SESSION_ID)
            rows["entity_id"].append(entity_id)
            rows["group"].append(st["group"])
            rows["frame_idx"].append(frame_idx)
            rows["time_master_ns"].append(t_ns)
            rows["x"].append(round(x, 4))
            rows["y"].append(round(y, 4))
            rows["speed"].append(round(speed, 4))
            rows["accel"].append(round(accel, 4))
            rows["heading_deg"].append(round(heading, 2))
            rows["orient_deg"].append(round(orient, 2))
            rows["dqi"].append(dqi)

    table = pa.table(
        rows,
        schema=pa.schema([
            ("session_id", pa.string()),
            ("entity_id", pa.string()),
            ("group", pa.string()),
            ("frame_idx", pa.int64()),
            ("time_master_ns", pa.int64()),
            ("x", pa.float64()),
            ("y", pa.float64()),
            ("speed", pa.float64()),
            ("accel", pa.float64()),
            ("heading_deg", pa.float64()),
            ("orient_deg", pa.float64()),
            ("dqi", pa.float64()),
        ]),
    )

    truth = {
        "n_frames": n_frames,
        "n_entities": N_ENTITIES,
        "n_observations": n_frames * N_ENTITIES,
        "groups": {g: ENTITIES_PER_GROUP for g in GROUPS},
        "low_quality_observations": int(sum(1 for q in rows["dqi"] if q < 0.5)),
    }
    return table, truth


def synthesize_scenes(rng: random.Random) -> pa.Table:
    """30 Hz scene reconstruction. Each row points at a 3D-reconstruction
    blob via URI; the metadata includes splat count and quality score.
    The blobs themselves do not exist — they are placeholders illustrating
    how a multi-megabyte stream attaches to the canonical timeline by
    reference, not by value.
    """
    n_scenes = SCENE_HZ * DURATION_S  # 900
    rows = {
        "session_id": [],
        "frame_master": [],            # which canonical Frame this scene aligns with (every 2nd Frame at 60 Hz)
        "time_master_ns": [],
        "scene_uri": [],
        "scene_size_bytes": [],
        "splat_count": [],
        "sqi": [],                     # scene quality index 0..1
    }
    for scene_idx in range(n_scenes):
        t_ns = scene_idx * (10**9 // SCENE_HZ)
        # 30 Hz scene aligns with every 2nd 60 Hz Frame
        master_frame = scene_idx * (TRACK_HZ // SCENE_HZ)
        rows["session_id"].append(SESSION_ID)
        rows["frame_master"].append(master_frame)
        rows["time_master_ns"].append(t_ns)
        rows["scene_uri"].append(
            f"obj://scenes/{SESSION_ID}/scene_{scene_idx:05d}.splat"
        )
        rows["scene_size_bytes"].append(rng.randint(2_000_000, 6_500_000))
        rows["splat_count"].append(rng.randint(80_000, 220_000))
        rows["sqi"].append(round(rng.uniform(0.85, 0.99), 4))

    return pa.table(
        rows,
        schema=pa.schema([
            ("session_id", pa.string()),
            ("frame_master", pa.int64()),
            ("time_master_ns", pa.int64()),
            ("scene_uri", pa.string()),
            ("scene_size_bytes", pa.int64()),
            ("splat_count", pa.int64()),
            ("sqi", pa.float64()),
        ]),
    )


def synthesize_imu(rng: random.Random) -> pa.Table:
    """200 Hz biomechanical telemetry on a single entity (alpha-00).
    Higher-rate than the canonical Frame timeline (200 / 60 ≈ 3.33×),
    illustrating how a denser stream stays attached to the master clock
    via predecessor + successor Frame indices.
    """
    n_samples = IMU_HZ * DURATION_S  # 6000
    rows = {
        "session_id": [],
        "entity_id": [],
        "t_unix_ns": [],               # absolute (sensor) clock
        "time_master_ns": [],          # mapped to canonical timeline
        "pred_frame": [],              # predecessor canonical Frame index
        "next_frame": [],              # successor canonical Frame index
        "gyro_x": [],
        "gyro_y": [],
        "gyro_z": [],
        "accel_x": [],
        "accel_y": [],
        "accel_z": [],
        "mag_x": [],
        "mag_y": [],
        "mag_z": [],
    }
    base_unix_ns = 1_730_000_000_000_000_000  # arbitrary epoch
    for s_idx in range(n_samples):
        t_master_ns = s_idx * (10**9 // IMU_HZ)
        t_unix_ns = base_unix_ns + t_master_ns
        # Map to canonical 60 Hz Frame: pred = floor, next = ceil
        approx_frame = (t_master_ns * TRACK_HZ) / 10**9
        pred_frame = int(approx_frame)
        next_frame = pred_frame + 1 if approx_frame > pred_frame else pred_frame

        rows["session_id"].append(SESSION_ID)
        rows["entity_id"].append("alpha-00")
        rows["t_unix_ns"].append(t_unix_ns)
        rows["time_master_ns"].append(t_master_ns)
        rows["pred_frame"].append(pred_frame)
        rows["next_frame"].append(next_frame)
        rows["gyro_x"].append(round(rng.gauss(0, 1.5), 4))
        rows["gyro_y"].append(round(rng.gauss(0, 1.5), 4))
        rows["gyro_z"].append(round(rng.gauss(0, 1.5), 4))
        rows["accel_x"].append(round(rng.gauss(0, 2.5), 4))
        rows["accel_y"].append(round(rng.gauss(0, 2.5), 4))
        rows["accel_z"].append(round(9.81 + rng.gauss(0, 0.5), 4))
        rows["mag_x"].append(round(rng.gauss(20, 1), 4))
        rows["mag_y"].append(round(rng.gauss(0, 1), 4))
        rows["mag_z"].append(round(rng.gauss(45, 1), 4))

    return pa.table(
        rows,
        schema=pa.schema([
            ("session_id", pa.string()),
            ("entity_id", pa.string()),
            ("t_unix_ns", pa.int64()),
            ("time_master_ns", pa.int64()),
            ("pred_frame", pa.int64()),
            ("next_frame", pa.int64()),
            ("gyro_x", pa.float64()), ("gyro_y", pa.float64()), ("gyro_z", pa.float64()),
            ("accel_x", pa.float64()), ("accel_y", pa.float64()), ("accel_z", pa.float64()),
            ("mag_x", pa.float64()), ("mag_y", pa.float64()), ("mag_z", pa.float64()),
        ]),
    )


def synthesize_events(rng: random.Random) -> pa.Table:
    """Sparse semantic event annotations across the session."""
    kinds = [
        "session_start", "phase_change", "key_event_a",
        "key_event_b", "key_event_c", "session_end",
    ]
    n_events = 30
    n_frames = TRACK_HZ * DURATION_S
    rows = {
        "session_id": [],
        "frame_master": [],
        "time_master_ns": [],
        "kind": [],
        "payload_json": [],
    }
    # Always anchor first + last
    rows["session_id"].extend([SESSION_ID, SESSION_ID])
    rows["frame_master"].extend([0, n_frames - 1])
    rows["time_master_ns"].extend([0, (n_frames - 1) * (10**9 // TRACK_HZ)])
    rows["kind"].extend(["session_start", "session_end"])
    rows["payload_json"].extend(['{"note":"begin"}', '{"note":"end"}'])

    for _ in range(n_events - 2):
        f = rng.randint(60, n_frames - 60)
        rows["session_id"].append(SESSION_ID)
        rows["frame_master"].append(f)
        rows["time_master_ns"].append(f * (10**9 // TRACK_HZ))
        rows["kind"].append(rng.choice(kinds[1:5]))
        rows["payload_json"].append('{"note":"transition"}')

    return pa.table(
        rows,
        schema=pa.schema([
            ("session_id", pa.string()),
            ("frame_master", pa.int64()),
            ("time_master_ns", pa.int64()),
            ("kind", pa.string()),
            ("payload_json", pa.string()),
        ]),
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20260501)

    tracking, truth = synthesize_tracking(rng)
    pq.write_table(tracking, OUT / "tracking.parquet", compression="snappy")
    print(f"wrote tracking.parquet ({tracking.num_rows:,} rows, "
          f"{(OUT / 'tracking.parquet').stat().st_size / 1024:.1f} KB)")

    scenes = synthesize_scenes(rng)
    pq.write_table(scenes, OUT / "scenes.parquet", compression="snappy")
    print(f"wrote scenes.parquet ({scenes.num_rows:,} rows, "
          f"{(OUT / 'scenes.parquet').stat().st_size / 1024:.1f} KB)")

    imu = synthesize_imu(rng)
    pq.write_table(imu, OUT / "imu.parquet", compression="snappy")
    print(f"wrote imu.parquet ({imu.num_rows:,} rows, "
          f"{(OUT / 'imu.parquet').stat().st_size / 1024:.1f} KB)")

    events = synthesize_events(rng)
    pq.write_table(events, OUT / "events.parquet", compression="snappy")
    print(f"wrote events.parquet ({events.num_rows:,} rows, "
          f"{(OUT / 'events.parquet').stat().st_size / 1024:.1f} KB)")

    truth["n_scenes"] = scenes.num_rows
    truth["n_imu"] = imu.num_rows
    truth["n_events"] = events.num_rows
    truth["session_id"] = SESSION_ID
    truth["track_hz"] = TRACK_HZ
    truth["scene_hz"] = SCENE_HZ
    truth["imu_hz"] = IMU_HZ
    truth["duration_s"] = DURATION_S

    (OUT / "ground_truth.json").write_text(json.dumps(truth, indent=2) + "\n")
    print(f"wrote ground_truth.json ({truth['n_observations']:,} expected observations)")


if __name__ == "__main__":
    main()
