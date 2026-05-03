"""Step 02 — Identity layer.

Verifies the singletons + Entity nodes load cleanly. This step is
runnable on its own as a smoke test, and surfaces the schema's
identity backbone (Session, Sensor, Group, Entity) before any
per-frame data lands.

Run:
    uv run python 02-identity-layer.py
"""
from __future__ import annotations

import time

from _load import load


def main() -> None:
    print("loading multi-stream world model...")
    t0 = time.perf_counter()
    db = load(verbose=True)
    elapsed = time.perf_counter() - t0
    print(f"\nload time: {elapsed:.1f}s")

    print("\n[1] Identity nodes:")
    for label in ("Session", "Sensor", "Group", "Entity"):
        n = db.execute(f"MATCH (n:{label}) RETURN count(n)").get(0, 0)
        print(f"    {label:30}{n}")

    print("\n[2] Group membership:")
    result = db.execute(
        "MATCH (e:Entity)-[:MEMBER_OF]->(g:Group) "
        "RETURN g.group_id AS group, count(e) AS members "
        "ORDER BY g.group_id"
    )
    for row in result:
        print(f"    {row['group']:30}{row['members']}")

    print("\n[3] Sensors and their declared coordinate frames:")
    result = db.execute(
        "MATCH (s:Sensor) "
        "RETURN s.sensor_id AS sensor, s.coordinate_frame AS frame, "
        "       s._observation_class AS obs_class "
        "ORDER BY s.sensor_id"
    )
    for row in result:
        print(f"    {row['sensor']:25}frame={row['frame']:20}class={row['obs_class']}")

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
