"""Shared loader used by every step that needs the world model in memory.

Each runnable step opens a fresh in-memory ArcFlow database and re-loads from
the synthesized Parquet files. Loading ~46K observations + auxiliary streams
takes ~10 seconds; for the recipe scale, re-loading per step is faster than
the disk round-trip would be and keeps every step independently runnable.

For a real session-scale workload (millions of frames, multiple hours), swap
this for a persistent ArcFlow path and load once. The recipe shape stays
identical.
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


def _esc(s: str) -> str:
    """Cypher single-quoted-string escape — for the recipe's known-safe inputs."""
    return s.replace("'", "\\'")


def load(verbose: bool = False) -> ArcFlow:
    """Load all four streams into a fresh in-memory ArcFlow.

    Returns the ArcFlow instance. The caller is responsible for closing it.

    Order:
        1. Singletons: Session + Sensor + Group nodes
        2. Entity nodes (with stable IDs and group membership)
        3. Frame nodes (60 Hz) + Frame.NEXT chain
        4. OBSERVED_AT edges (Entity -> Frame, with kinematics + confidence)
        5. SceneReconstruction nodes + HAS_SCENE edges
        6. BiomechanicalSample nodes + SAMPLED_AT edges
        7. Event nodes + ANCHORED_AT edges
    """
    require_sample_data()
    truth = ground_truth()

    db = ArcFlow()  # in-memory

    # 0. Indexes BEFORE bulk inserts.
    #
    # NOTE(invariant): every node label that gets MATCH-looked-up by a
    #   property in the hot path needs a CREATE INDEX declaration first.
    #   Without it, find_nodes() falls through to a per-label column scan
    #   (O(N)) instead of the property_index hit (O(1)). At a few hundred
    #   nodes the difference is in the noise; at 50K+ nodes per label the
    #   curve diverges sharply (the football-transformer alpha eval hit
    #   <100 writes/sec at the 1M-edge / 46K-frame mark without these).
    #
    # Index everything on the hot path: Entity by entity_id, Frame by
    # frame_idx (the two MATCH lookups every OBSERVED_AT insert does),
    # plus the auxiliary-stream join keys.
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
    db.execute(
        f"CREATE (:Session {{"
        f"  session_id: '{_esc(truth['session_id'])}',"
        f"  duration_s: {truth['duration_s']},"
        f"  track_hz: {truth['track_hz']},"
        f"  scene_hz: {truth['scene_hz']},"
        f"  imu_hz: {truth['imu_hz']}"
        f"}})"
    )
    for sensor in ("primary_tracker", "scene_reconstructor", "imu_unit"):
        db.execute(
            f"CREATE (:Sensor {{"
            f"  sensor_id: '{sensor}',"
            f"  coordinate_frame: 'session-local',"
            f"  _observation_class: 'observed'"
            f"}})"
        )
    for group in ("alpha", "beta"):
        db.execute(
            f"CREATE (:Group {{group_id: '{group}', session_id: '{_esc(truth['session_id'])}'}})"
        )

    # 2. Entity nodes
    for group in ("alpha", "beta"):
        for n in range(11):
            entity_id = f"{group}-{n:02d}"
            db.execute(
                f"CREATE (:Entity {{"
                f"  entity_id: '{entity_id}', group_id: '{group}'"
                f"}})"
            )
            # MEMBER_OF edge with observation class
            db.execute(
                f"MATCH (e:Entity {{entity_id: '{entity_id}'}}),"
                f"      (g:Group {{group_id: '{group}'}})"
                f" CREATE (e)-[:MEMBER_OF {{"
                f"  _observation_class: 'observed', _confidence: 1.0"
                f"}}]->(g)"
            )

    # 3. Frame nodes at 60 Hz.
    # NOTE: The schema (see README.md "Schema design") describes Frame.NEXT
    # as an explicit linked list. At recipe scale (~hundreds of frames per second
    # of session) the per-edge MATCH+CREATE round-trip dominates load time
    # and trajectory queries can ORDER BY frame_idx for the same result.
    # NEXT is left for a future production-shape variant where bulk-load
    # primitives (FlatSpatialIndex::bulk_load, batched CREATE) avoid the
    # round-trip cost.
    n_frames = truth["n_frames"]
    if verbose:
        print(f"  creating {n_frames} Frame nodes...")
    for f in range(n_frames):
        t_ns = f * (10**9 // truth["track_hz"])
        db.execute(
            f"CREATE (:Frame {{"
            f"  session_id: '{_esc(truth['session_id'])}',"
            f"  frame_idx: {f},"
            f"  time_master_ns: {t_ns}"
            f"}})"
        )

    # 4. OBSERVED_AT edges — the heavy lift
    if verbose:
        print(f"  loading tracking observations ({truth['n_observations']:,})...")
    rows = pq.read_table(DATA / "tracking.parquet").to_pylist()
    for r in rows:
        db.execute(
            "MATCH (e:Entity {entity_id: '" + r["entity_id"] + "'}),"
            f"      (f:Frame {{frame_idx: {r['frame_idx']}}})"
            f" CREATE (e)-[:OBSERVED_AT {{"
            f"  x: {r['x']}, y: {r['y']},"
            f"  speed: {r['speed']}, accel: {r['accel']},"
            f"  heading_deg: {r['heading_deg']}, orient_deg: {r['orient_deg']},"
            f"  _confidence: {r['dqi']},"
            f"  _observation_class: 'observed',"
            f"  _source: 'primary_tracker'"
            f"}}]->(f)"
        )

    # 5. SceneReconstruction nodes + HAS_SCENE edges.
    # NOTE: split into two execute() calls per scene — single-statement
    # MATCH+CREATE node+CREATE edge doesn't reliably persist the edge in
    # the alpha query path. Two-step (CREATE node, then MATCH-both+CREATE
    # edge) is the durable shape the rest of the recipe relies on.
    if verbose:
        print(f"  loading {truth['n_scenes']} scene reconstructions...")
    for r in pq.read_table(DATA / "scenes.parquet").to_pylist():
        scene_id = f"scene-{int(r['frame_master']):06d}"
        db.execute(
            f"CREATE (:SceneReconstruction {{"
            f"  scene_id: '{scene_id}',"
            f"  frame_master: {r['frame_master']},"
            f"  session_id: '{_esc(r['session_id'])}',"
            f"  scene_uri: '{_esc(r['scene_uri'])}',"
            f"  scene_size_bytes: {r['scene_size_bytes']},"
            f"  splat_count: {r['splat_count']},"
            f"  _confidence: {r['sqi']},"
            f"  _observation_class: 'observed',"
            f"  _source: 'scene_reconstructor'"
            f"}})"
        )
        db.execute(
            f"MATCH (f:Frame {{frame_idx: {r['frame_master']}}}),"
            f"      (s:SceneReconstruction {{scene_id: '{scene_id}'}})"
            f" CREATE (f)-[:HAS_SCENE]->(s)"
        )

    # 6. BiomechanicalSample nodes + SAMPLED_AT edges (only on alpha-00).
    # Same two-step pattern as scenes.
    if verbose:
        print(f"  loading {truth['n_imu']} biomechanical samples...")
    for r in pq.read_table(DATA / "imu.parquet").to_pylist():
        sample_id = f"imu-{r['time_master_ns']}"
        db.execute(
            f"CREATE (:BiomechanicalSample {{"
            f"  sample_id: '{sample_id}',"
            f"  t_unix_ns: {r['t_unix_ns']},"
            f"  time_master_ns: {r['time_master_ns']},"
            f"  pred_frame: {r['pred_frame']},"
            f"  next_frame: {r['next_frame']},"
            f"  gyro_x: {r['gyro_x']}, gyro_y: {r['gyro_y']}, gyro_z: {r['gyro_z']},"
            f"  accel_x: {r['accel_x']}, accel_y: {r['accel_y']}, accel_z: {r['accel_z']},"
            f"  _observation_class: 'observed',"
            f"  _confidence: 0.95,"
            f"  _source: 'imu_unit',"
            f"  _coordinate_frame: 'sensor-local'"
            f"}})"
        )
        db.execute(
            "MATCH (e:Entity {entity_id: 'alpha-00'}),"
            f"      (b:BiomechanicalSample {{sample_id: '{sample_id}'}})"
            f" CREATE (e)-[:SAMPLED_AT]->(b)"
        )

    # 7. Event nodes + ANCHORED_AT edges (two-step pattern).
    if verbose:
        print(f"  loading {truth['n_events']} events...")
    for ev_idx, r in enumerate(pq.read_table(DATA / "events.parquet").to_pylist()):
        event_id = f"event-{ev_idx:06d}"
        db.execute(
            f"CREATE (:Event {{"
            f"  event_id: '{event_id}',"
            f"  kind: '{_esc(r['kind'])}',"
            f"  frame_master: {r['frame_master']},"
            f"  time_master_ns: {r['time_master_ns']},"
            f"  payload: '{_esc(r['payload_json'])}',"
            f"  _observation_class: 'observed'"
            f"}})"
        )
        db.execute(
            f"MATCH (ev:Event {{event_id: '{event_id}'}}),"
            f"      (f:Frame {{frame_idx: {r['frame_master']}}})"
            f" CREATE (ev)-[:ANCHORED_AT]->(f)"
        )

    if verbose:
        print(f"  loaded session={truth['session_id']}: "
              f"{truth['n_frames']} Frames, {truth['n_entities']} Entities, "
              f"{truth['n_observations']:,} OBSERVED_AT, "
              f"{truth['n_scenes']} SceneReconstruction, "
              f"{truth['n_imu']} BiomechanicalSample, "
              f"{truth['n_events']} Event")

    return db
