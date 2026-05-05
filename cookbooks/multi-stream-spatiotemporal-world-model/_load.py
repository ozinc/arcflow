"""Shared loader used by every step that needs the world model in memory.

Each runnable step opens a fresh in-memory ArcFlow database and re-loads from
the synthesized Parquet files. The bulk APIs (``bulk_create_nodes`` /
``bulk_create_relationships``) load ~46K Frames + ~20K observations + the
auxiliary streams in well under a second — fast enough that re-loading per
step is preferable to a disk round-trip and keeps every step independently
runnable.

For a real session-scale workload (millions of frames, multiple hours), swap
this for a persistent ArcFlow path and load once. The recipe shape stays
identical.

The bulk-array path bypasses the Cypher parser entirely and writes at
~1M ops/sec — the right tool for any workload where you already have a
list of rows in Python (sensor streams, batch ingest, parquet pipelines).
"""
from __future__ import annotations

import json
from pathlib import Path

import pyarrow.parquet as pq

from arcflow import ArcFlow

HERE = Path(__file__).parent
DATA = HERE / "data" / "sample"


def require_sample_data() -> None:
    if not DATA.exists() or not (DATA / "tracking.parquet").exists():
        raise SystemExit(
            f"Missing sample data under {DATA}. Run 00-make-sample.py first."
        )


def ground_truth() -> dict:
    require_sample_data()
    return json.loads((DATA / "ground_truth.json").read_text())


def load(verbose: bool = False) -> ArcFlow:
    """Load all four streams into a fresh in-memory ArcFlow.

    Returns the ArcFlow instance. The caller is responsible for closing it.

    Order:
        1. Singletons: Session + Sensor + Group nodes
        2. Entity nodes (with stable IDs and group membership)
        3. Frame nodes (60 Hz)
        4. OBSERVED_AT edges (Entity -> Frame, with kinematics + confidence)
        5. SceneReconstruction nodes + HAS_SCENE edges
        6. BiomechanicalSample nodes + SAMPLED_AT edges
        7. Event nodes + ANCHORED_AT edges

    All node/edge creates use the typed bulk APIs (`bulk_create_nodes` /
    `bulk_create_relationships`) — single MVCC transaction per call, no
    per-row parser cost.
    """
    require_sample_data()
    truth = ground_truth()

    db = ArcFlow()  # in-memory

    # 0. Indexes BEFORE bulk inserts.
    #
    # Bulk-create-edges takes NodeIds directly (no MATCH lookup), so the
    # explicit indexes below are not strictly required for the bulk path.
    # We keep them because *query-time* MATCH-by-property lookups in the
    # downstream cookbook steps still benefit (and stay O(1)).
    for stmt in (
        "CREATE INDEX ON :Entity(entity_id)",
        "CREATE INDEX ON :Frame(frame_idx)",
        "CREATE INDEX ON :SceneReconstruction(scene_id)",
        "CREATE INDEX ON :BiomechanicalSample(sample_id)",
        "CREATE INDEX ON :Event(event_id)",
        "CREATE INDEX ON :Group(group_id)",
    ):
        db.execute(stmt)

    # 1. Session singleton + Sensor singletons + Groups
    db.bulk_create_nodes([
        (["Session"], {
            "session_id": truth["session_id"],
            "duration_s": truth["duration_s"],
            "track_hz": truth["track_hz"],
            "scene_hz": truth["scene_hz"],
            "imu_hz": truth["imu_hz"],
        }),
    ])
    db.bulk_create_nodes([
        (["Sensor"], {
            "sensor_id": s,
            "coordinate_frame": "session-local",
            "_observation_class": "observed",
        })
        for s in ("primary_tracker", "scene_reconstructor", "imu_unit")
    ])
    group_ids = db.bulk_create_nodes([
        (["Group"], {"group_id": g, "session_id": truth["session_id"]})
        for g in ("alpha", "beta")
    ])
    group_id_by_name = {"alpha": group_ids[0], "beta": group_ids[1]}

    # 2. Entity nodes — bulk-create, then bulk-create the MEMBER_OF edges
    # in one parallel-array call.
    entity_specs = [
        (group, n)
        for group in ("alpha", "beta")
        for n in range(11)
    ]
    entity_ids = db.bulk_create_nodes([
        (["Entity"], {
            "entity_id": f"{group}-{n:02d}",
            "group_id": group,
        })
        for group, n in entity_specs
    ])
    entity_id_by_name = {
        f"{group}-{n:02d}": eid
        for (group, n), eid in zip(entity_specs, entity_ids)
    }
    db.bulk_create_relationships(
        "MEMBER_OF",
        [
            (entity_ids[i], group_id_by_name[group], {
                "_observation_class": "observed",
                "_confidence": 1.0,
            })
            for i, (group, _n) in enumerate(entity_specs)
        ],
    )

    # 3. Frame nodes at 60 Hz — one bulk call.
    n_frames = truth["n_frames"]
    if verbose:
        print(f"  creating {n_frames} Frame nodes...")
    frame_ids = db.bulk_create_nodes([
        (["Frame"], {
            "session_id": truth["session_id"],
            "frame_idx": f,
            "time_master_ns": f * (10**9 // truth["track_hz"]),
        })
        for f in range(n_frames)
    ])
    # frame_idx == position in list, so frame_ids[idx] gives the NodeId.

    # 4. OBSERVED_AT edges — the heavy lift. ~20K edges in well under 100ms
    # via parallel-array bulk-create.
    if verbose:
        print(f"  loading tracking observations ({truth['n_observations']:,})...")
    rows = pq.read_table(DATA / "tracking.parquet").to_pylist()
    obs_edges = [
        (
            entity_id_by_name[r["entity_id"]],
            frame_ids[r["frame_idx"]],
            {
                "x": r["x"], "y": r["y"],
                "speed": r["speed"], "accel": r["accel"],
                "heading_deg": r["heading_deg"], "orient_deg": r["orient_deg"],
                "_confidence": r["dqi"],
                "_observation_class": "observed",
                "_source": "primary_tracker",
            },
        )
        for r in rows
    ]
    db.bulk_create_relationships("OBSERVED_AT", obs_edges)

    # 5. SceneReconstruction nodes + HAS_SCENE edges.
    if verbose:
        print(f"  loading {truth['n_scenes']} scene reconstructions...")
    scene_rows = pq.read_table(DATA / "scenes.parquet").to_pylist()
    scene_ids = db.bulk_create_nodes([
        (["SceneReconstruction"], {
            "scene_id": f"scene-{int(r['frame_master']):06d}",
            "frame_master": r["frame_master"],
            "session_id": r["session_id"],
            "scene_uri": r["scene_uri"],
            "scene_size_bytes": r["scene_size_bytes"],
            "splat_count": r["splat_count"],
            "_confidence": r["sqi"],
            "_observation_class": "observed",
            "_source": "scene_reconstructor",
        })
        for r in scene_rows
    ])
    db.bulk_create_relationships(
        "HAS_SCENE",
        [
            (frame_ids[int(r["frame_master"])], scene_ids[i], {})
            for i, r in enumerate(scene_rows)
        ],
    )

    # 6. BiomechanicalSample nodes + SAMPLED_AT edges (only on alpha-00).
    if verbose:
        print(f"  loading {truth['n_imu']} biomechanical samples...")
    imu_rows = pq.read_table(DATA / "imu.parquet").to_pylist()
    imu_ids = db.bulk_create_nodes([
        (["BiomechanicalSample"], {
            "sample_id": f"imu-{r['time_master_ns']}",
            "t_unix_ns": r["t_unix_ns"],
            "time_master_ns": r["time_master_ns"],
            "pred_frame": r["pred_frame"],
            "next_frame": r["next_frame"],
            "gyro_x": r["gyro_x"], "gyro_y": r["gyro_y"], "gyro_z": r["gyro_z"],
            "accel_x": r["accel_x"], "accel_y": r["accel_y"], "accel_z": r["accel_z"],
            "_observation_class": "observed",
            "_confidence": 0.95,
            "_source": "imu_unit",
            "_coordinate_frame": "sensor-local",
        })
        for r in imu_rows
    ])
    alpha00_id = entity_id_by_name["alpha-00"]
    db.bulk_create_relationships(
        "SAMPLED_AT",
        [(alpha00_id, sid, {}) for sid in imu_ids],
    )

    # 7. Event nodes + ANCHORED_AT edges.
    if verbose:
        print(f"  loading {truth['n_events']} events...")
    event_rows = pq.read_table(DATA / "events.parquet").to_pylist()
    event_ids = db.bulk_create_nodes([
        (["Event"], {
            "event_id": f"event-{i:06d}",
            "kind": r["kind"],
            "frame_master": r["frame_master"],
            "time_master_ns": r["time_master_ns"],
            "payload": r["payload_json"],
            "_observation_class": "observed",
        })
        for i, r in enumerate(event_rows)
    ])
    db.bulk_create_relationships(
        "ANCHORED_AT",
        [
            (eid, frame_ids[int(r["frame_master"])], {})
            for eid, r in zip(event_ids, event_rows)
        ],
    )

    if verbose:
        print(f"  loaded session={truth['session_id']}: "
              f"{truth['n_frames']} Frames, {truth['n_entities']} Entities, "
              f"{truth['n_observations']:,} OBSERVED_AT, "
              f"{truth['n_scenes']} SceneReconstruction, "
              f"{truth['n_imu']} BiomechanicalSample, "
              f"{truth['n_events']} Event")

    return db
