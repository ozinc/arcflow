"""Step 08 — Temporal query showcase.

Demonstrates ArcFlow's temporal primitives over the 60 Hz Frame timeline:

  - per-entity trajectory (ordered streaming over OBSERVED_AT)
  - frame-aligned window — state at the moment of an event
  - cross-stream join (entity tracking + auxiliary scene reconstruction)
  - confidence-filtered retrieval

Run:
    uv run python 08-temporal-queries.py
"""
from __future__ import annotations

from _load import load


def main() -> None:
    db = load()

    target_entity = "alpha-00"

    print(f"\n[1] Trajectory for {target_entity} (first 5 frames):")
    result = db.execute(
        "MATCH (e:Entity {entity_id: '" + target_entity + "'})-[r:OBSERVED_AT]->(f:Frame) "
        "RETURN f.frame_idx AS frame, r.x AS x, r.y AS y, r.speed AS speed "
        "ORDER BY f.frame_idx "
        "LIMIT 5"
    )
    for row in result:
        print(
            f"    frame={int(row['frame']):>4}  "
            f"x={float(row['x']):6.2f}  y={float(row['y']):5.2f}  "
            f"speed={float(row['speed']):.2f}"
        )

    print(f"\n[2] Average speed per entity per group (top 5):")
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->() "
        "RETURN e.entity_id AS entity, e.group_id AS group, avg(r.speed) AS avg_speed "
        "ORDER BY avg_speed DESC "
        "LIMIT 5"
    )
    for row in result:
        print(
            f"    {row['entity']:12}({row['group']})  "
            f"avg_speed={float(row['avg_speed']):.3f}"
        )

    print("\n[3] Event-anchored snapshot — state at every 'phase_change' event:")
    result = db.execute(
        "MATCH (ev:Event {kind: 'phase_change'})-[:ANCHORED_AT]->(f:Frame) "
        "RETURN f.frame_idx AS frame "
        "ORDER BY f.frame_idx "
        "LIMIT 3"
    )
    phase_change_frames = [int(row["frame"]) for row in result]
    print(f"    phase_change frames (first 3): {phase_change_frames}")

    if phase_change_frames:
        f0 = phase_change_frames[0]
        result = db.execute(
            "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
            f"WHERE f.frame_idx = {f0} "
            "RETURN e.entity_id AS entity, r.x AS x, r.y AS y "
            "ORDER BY entity "
            "LIMIT 3"
        )
        print(f"    state at frame {f0} (3 of 22 entities):")
        for row in result:
            print(
                f"      {row['entity']:12}x={float(row['x']):6.2f}  y={float(row['y']):5.2f}"
            )

    print("\n[4] Cross-stream — Frames that have both tracking AND a scene reconstruction:")
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame)-[:HAS_SCENE]->(s:SceneReconstruction) "
        "RETURN count(DISTINCT f) AS frames_with_both"
    )
    print(f"    frames with tracking + scene: {int(result.get(0, 0))}")

    print("\n[5] Confidence-filtered retrieval — high-trust observations only:")
    n_total = int(
        db.execute("MATCH ()-[r:OBSERVED_AT]->() RETURN count(r)").get(0, 0)
    )
    n_trusted = int(
        db.execute(
            "MATCH ()-[r:OBSERVED_AT]->() "
            "WHERE r._confidence > 0.9 AND r._observation_class = 'observed' "
            "RETURN count(r)"
        ).get(0, 0)
    )
    print(
        f"    observed + _confidence > 0.9:  {n_trusted:,} / {n_total:,} "
        f"({n_trusted / n_total * 100:.1f}%)"
    )

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
