"""Step 07 — Spatial query showcase.

Shows the spatial primitives that work cleanly through the alpha Python
binding today:

  - per-frame snapshot (everyone at a single tick)
  - bounding-box / region scan (entities inside a defined zone)
  - K-nearest-neighbours via x/y bounding-box pre-filter + Python-side
    distance ranking (sub-100 ms even for 22 entities × 900 frames)

The bounding-box approach scales: ArcFlow's spatial index narrows the
candidate set to a few entities, Python ranks them by exact distance.
For raw `nearestNodes` / `distance` primitives operating natively in
WorldCypher, see the production deployment guide — those land cleanly
through the TypeScript binding today.

Run:
    uv run python 07-spatial-queries.py
"""
from __future__ import annotations

import math

from _load import load


def main() -> None:
    db = load()

    target_frame = 250        # ~4.17s into the 15s session at 60 Hz
    target_entity = "alpha-00"

    print(f"\n[1] Per-frame snapshot at frame_idx={target_frame} (sorted by x):")
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
        f"WHERE f.frame_idx = {target_frame} "
        "RETURN e.entity_id AS entity, e.group_id AS group, r.x AS x, r.y AS y "
        "ORDER BY r.x "
        "LIMIT 5"
    )
    print(f"    rows: {result.row_count}  (showing 5 of 22)")
    for row in result:
        print(
            f"    {row['entity']:12}({row['group']})  "
            f"x={float(row['x']):6.2f}  y={float(row['y']):5.2f}"
        )

    print(f"\n[2] Region scan — entities inside bounding box x:[40,80] y:[20,60] at frame {target_frame}:")
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
        f"WHERE f.frame_idx = {target_frame} "
        "  AND r.x >= 40.0 AND r.x <= 80.0 "
        "  AND r.y >= 20.0 AND r.y <= 60.0 "
        "RETURN e.entity_id AS entity, r.x AS x, r.y AS y "
        "ORDER BY entity"
    )
    print(f"    inside: {result.row_count}")
    for row in result:
        print(f"    {row['entity']:12}x={float(row['x']):6.2f}  y={float(row['y']):5.2f}")

    print(f"\n[3] K-nearest cross-group entities to {target_entity} at frame {target_frame}:")
    print(f"    (bbox pre-filter via spatial index, Python-side exact distance ranking)")
    target = db.execute(
        "MATCH (e:Entity {entity_id: '" + target_entity + "'})-[r:OBSERVED_AT]->(f:Frame) "
        f"WHERE f.frame_idx = {target_frame} "
        "RETURN r.x AS x, r.y AS y"
    )
    tx = float(target.get(0, 0))
    ty = float(target.get(0, 1))
    print(f"    {target_entity} at ({tx:.2f}, {ty:.2f})")

    # Spatial pre-filter: 25-yard bbox around the target — bbox uses index
    bbox = 25.0
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
        f"WHERE f.frame_idx = {target_frame} "
        f"  AND e.group_id <> 'alpha' "
        f"  AND r.x >= {tx - bbox} AND r.x <= {tx + bbox} "
        f"  AND r.y >= {ty - bbox} AND r.y <= {ty + bbox} "
        "RETURN e.entity_id AS entity, r.x AS x, r.y AS y"
    )
    candidates = [
        (row["entity"], float(row["x"]), float(row["y"]))
        for row in result
    ]
    ranked = sorted(
        candidates,
        key=lambda c: math.hypot(c[1] - tx, c[2] - ty),
    )
    print(f"    {len(candidates)} candidates within {bbox} yd, ranked by exact distance:")
    for name, x, y in ranked[:5]:
        d = math.hypot(x - tx, y - ty)
        print(f"      {name:12}distance={d:6.2f}  at ({x:.2f}, {y:.2f})")

    print(f"\n[4] Standing geofence — count of entities inside the central zone over the session:")
    print(f"    (sample every 100 frames = 1.67s)")
    for frame in range(0, 900, 100):
        n = int(
            db.execute(
                "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
                f"WHERE f.frame_idx = {frame} "
                "  AND r.x >= 50.0 AND r.x <= 70.0 "
                "  AND r.y >= 30.0 AND r.y <= 50.0 "
                "RETURN count(e)"
            ).get(0, 0)
        )
        print(f"    frame {frame:>4}  zone occupancy: {n}")

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
