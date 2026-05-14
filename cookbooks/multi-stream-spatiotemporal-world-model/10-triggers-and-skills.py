"""Step 10 — Triggers and behavior-graph SKILLs.

Conceptually:

    CREATE TRIGGER zone_entry
      ON :Frame WHEN CREATED
      RUN SKILL classify_zone_occupancy

A TRIGGER is a fire-once event binding. When a Frame node is
inserted, the engine evaluates the trigger's condition and, if matched,
invokes a SKILL — either a built-in behavior procedure or a registered
external action. SKILLs are relationship constructors that operate over
the recently-changed subgraph.

In TypeScript, the engine fires the callback on every Frame insert
(20 ms tail latency at 60 Hz). In Python today, this step demonstrates
the SHAPE of trigger evaluation by walking the frames and applying the
same condition+action logic explicitly. The pattern is identical; only
the dispatch site differs.

Run:
    uv run python 10-triggers-and-skills.py
"""
from __future__ import annotations

import math

from _load import load


def main() -> None:
    db = load()

    print("\n[1] State-transition trigger — fires when zone occupancy crosses 5:")
    print("    (Conceptual TRIGGER: ON :Frame WHEN CREATED)")
    prev_count = 0
    transitions = 0
    for frame in range(0, 900, 30):     # sample every 30 frames (= 0.5 s) for brevity
        n = int(
            db.execute(
                "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
                f"WHERE f.frame_idx = {frame} "
                "  AND r.x >= 50.0 AND r.x <= 70.0 "
                "  AND r.y >= 30.0 AND r.y <= 50.0 "
                "RETURN count(e)"
            ).get(0, 0)
        )
        if (prev_count < 5 and n >= 5) or (prev_count >= 5 and n < 5):
            transitions += 1
            direction = "RISE" if n >= 5 else "FALL"
            print(f"    frame {frame:>4}  TRIGGER FIRED ({direction})  occupancy {prev_count}→{n}")
        prev_count = n
    print(f"    total transitions: {transitions}")

    print("\n[2] Anomaly trigger — fires on Frames where any tracking _confidence < 0.5:")
    print("    (Conceptual TRIGGER: ON :Frame WHEN CREATED IF EXISTS low-confidence observation)")
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
        "WHERE r._confidence < 0.5 "
        "RETURN f.frame_idx AS frame, e.entity_id AS entity, r._confidence AS conf "
        "ORDER BY frame "
        "LIMIT 5"
    )
    n_low = result.row_count
    print(f"    frames with low-confidence observations (showing first {min(5, n_low)}):")
    for row in result:
        print(
            f"      frame {int(row['frame']):>4}  entity={row['entity']}  "
            f"_confidence={float(row['conf']):.3f}"
        )

    print("\n[3] Cross-stream trigger — fires on scenes with unusually large reconstruction:")
    print("    (Conceptual TRIGGER: ON :SceneReconstruction WHEN CREATED IF size_bytes > 6_000_000)")
    result = db.execute(
        "MATCH (s:SceneReconstruction) "
        "WHERE s.scene_size_bytes > 6000000 "
        "RETURN s.frame_master AS frame, s.splat_count AS splats, "
        "       s.scene_size_bytes AS size_bytes "
        "ORDER BY size_bytes DESC "
        "LIMIT 3"
    )
    print(f"    high-detail scenes (top 3 of {result.row_count}):")
    for row in result:
        size_mb = float(row["size_bytes"]) / 1024 / 1024
        print(
            f"      frame {int(row['frame']):>4}  "
            f"splats={int(row['splats']):>7,}  size={size_mb:.2f} MB"
        )

    print("\n[4] Composed trigger — proximity event detection (typical SKILL shape):")
    print(
        "    (Conceptual SKILL: classify_proximity_event\n"
        "     INPUTS: pair-of-entities, proximity-distance, frame_idx\n"
        "     OUTPUTS: Event {kind: 'proximity_alert'} ANCHORED_AT Frame)"
    )
    # Pull positions for ALL entities at the test frame; compute proximity events in Python
    test_frame = 200
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
        f"WHERE f.frame_idx = {test_frame} "
        "RETURN e.entity_id AS entity, e.group_id AS group, r.x AS x, r.y AS y"
    )
    entities = [(row["entity"], row["group"], float(row["x"]), float(row["y"])) for row in result]
    alpha = [e for e in entities if e[1] == "alpha"]
    beta = [e for e in entities if e[1] == "beta"]
    threshold = 5.0
    events = []
    for ea, _, xa, ya in alpha:
        for eb, _, xb, yb in beta:
            d = math.hypot(xa - xb, ya - yb)
            if d < threshold:
                events.append((ea, eb, d))
    print(f"    cross-group close-encounter events at frame {test_frame} (within {threshold} yd):")
    if events:
        for ea, eb, d in sorted(events, key=lambda x: x[2])[:5]:
            print(f"      {ea:10}↔ {eb:10}distance={d:.2f}")
    else:
        print(f"      (none — try threshold > 8.0 if no events at this frame)")

    db.close()
    print(
        "\nOK\n\n"
        "Pattern note: triggers and SKILLs compose at runtime — the engine\n"
        "evaluates trigger conditions on every relevant mutation and\n"
        "dispatches SKILLs via an executor IPC bridge that keeps DNN\n"
        "inference and other heavy logic in a separate crash domain. This\n"
        "step demonstrates the LOGIC; production deployments wire the\n"
        "dispatch via CREATE TRIGGER / CREATE SKILL."
    )


if __name__ == "__main__":
    main()
