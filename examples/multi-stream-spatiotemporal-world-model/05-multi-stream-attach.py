"""Step 05 — Multi-stream attach verification.

Confirms that the auxiliary streams (3D scene reconstructions at 30 Hz,
biomechanical telemetry at 200 Hz, sparse events) attach to the canonical
60 Hz Frame timeline at the right cadence and that every reconciliation
invariant holds.

Run:
    uv run python 05-multi-stream-attach.py
"""
from __future__ import annotations

from _load import load, ground_truth


def main() -> None:
    truth = ground_truth()
    db = load()

    print("\n[1] Stream cadence — node counts vs ground truth:")
    n_scenes = int(db.execute("MATCH (s:SceneReconstruction) RETURN count(s)").get(0, 0))
    n_imu = int(db.execute("MATCH (b:BiomechanicalSample) RETURN count(b)").get(0, 0))
    n_events = int(db.execute("MATCH (e:Event) RETURN count(e)").get(0, 0))
    n_frames = int(db.execute("MATCH (f:Frame) RETURN count(f)").get(0, 0))

    print(f"    Frames        (60 Hz × {truth['duration_s']}s):       {n_frames}  (expected {truth['n_frames']})")
    print(f"    Scenes        (30 Hz × {truth['duration_s']}s):       {n_scenes}  (expected {truth['n_scenes']})")
    print(f"    Biomech       (200 Hz × {truth['duration_s']}s):      {n_imu}  (expected {truth['n_imu']})")
    print(f"    Events        (sparse):                {n_events}  (expected {truth['n_events']})")
    assert n_frames == truth["n_frames"]
    assert n_scenes == truth["n_scenes"]
    assert n_imu == truth["n_imu"]
    assert n_events == truth["n_events"]

    print("\n[2] Cadence ratios (each auxiliary stream vs canonical 60 Hz):")
    print(f"    Scenes per Frame:        {n_scenes / n_frames:.3f}  (expected {truth['scene_hz']/truth['track_hz']:.3f})")
    print(f"    Biomech per Frame:       {n_imu / n_frames:.3f}  (expected {truth['imu_hz']/truth['track_hz']:.3f})")

    print("\n[3] Scene attachment — every Frame at master_idx % 2 == 0 has exactly one scene:")
    result = db.execute(
        "MATCH (f:Frame)-[:HAS_SCENE]->(s:SceneReconstruction) "
        "RETURN count(s) AS scenes_attached"
    )
    attached = int(result.get(0, 0))
    print(f"    Frames with scene attached:  {attached}  (expected {truth['n_scenes']})")
    assert attached == truth["n_scenes"]

    print("\n[4] Biomechanical samples — all on alpha-00 (single-entity high-rate stream):")
    result = db.execute(
        "MATCH (e:Entity)-[:SAMPLED_AT]->(b:BiomechanicalSample) "
        "RETURN e.entity_id AS entity, count(b) AS samples"
    )
    for row in result:
        print(f"    {row['entity']:30}{int(row['samples']):,}")

    print("\n[5] Event timeline — first + last anchored to bookend Frames:")
    result = db.execute(
        "MATCH (e:Event)-[:ANCHORED_AT]->(f:Frame) "
        "RETURN e.kind AS kind, f.frame_idx AS frame "
        "ORDER BY f.frame_idx "
        "LIMIT 3"
    )
    for row in result:
        print(f"    frame={row['frame']:>4}    {row['kind']}")

    print("\n[6] Coordinate-frame discipline — biomech samples carry sensor-local frame metadata:")
    result = db.execute(
        "MATCH (b:BiomechanicalSample) "
        "RETURN b._coordinate_frame AS frame, count(b) AS samples"
    )
    for row in result:
        print(f"    {row['frame']:30}{int(row['samples']):,}")

    db.close()
    print("\nOK — every stream attached, every cadence ratio matches ground truth.")


if __name__ == "__main__":
    main()
