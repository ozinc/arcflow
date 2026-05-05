"""
Robotics control replay — what did the robot's world model show when the avoid-action fired?

Pattern: a robot's world model is updated continuously from sensors.
At some moment, a control loop fires an avoid-action. Engineers need to
reconstruct the exact world state that triggered it — for safety review,
for tuning, for blame allocation between perception and policy.

`AS OF seq <param>` reads the world at the trigger moment.

Setup: an Obstacle is observed, the robot's distance estimate updates
over time, and an avoid-action is recorded. Replay shows the
distance / confidence the controller saw at decision time.
"""

import shutil
import tempfile

from arcflow import ArcFlow

def main():
    data_dir = tempfile.mkdtemp(prefix="arcflow-robotics-replay-")
    db = ArcFlow(data_dir)

    # Seq 1: obstacle first detected far away.
    db.execute("""
        CREATE (o:Obstacle {
            id: 'obs-1',
            distance_m: 12.5,
            confidence: 0.62
        })
    """)
    print("seq 1: obstacle first detected (distance=12.5m, confidence=0.62)")

    # Seqs 2, 3: distance + confidence improve as obstacle gets closer.
    db.execute("""
        MATCH (o:Obstacle {id: 'obs-1'})
        SET o.distance_m = 8.4,
            o.confidence = 0.81
    """)
    # Comma-SET produces ONE WAL entry per assignment — fine-grained audit.
    print("seq 2: distance updated → 8.4m")
    print("seq 3: confidence updated → 0.81")

    # Seq 4: closer still — and this is the moment the controller fires
    # the avoid-action.
    db.execute("""
        MATCH (o:Obstacle {id: 'obs-1'})
        SET o.distance_m = 3.1,
            o.confidence = 0.93
    """)
    print("seq 4: distance updated → 3.1m")
    print("seq 5: confidence updated → 0.93 ← AVOID-ACTION FIRES at this seq")
    avoid_seq = 5

    # Seq 6: robot manoeuvres; obstacle reading shifts as the robot moves.
    db.execute("""
        MATCH (o:Obstacle {id: 'obs-1'})
        SET o.distance_m = 4.5
    """)
    print("seq 6: post-manoeuvre, distance = 4.5m")

    # The post-incident question: what did the controller see?
    print(f"\nAS OF seq {avoid_seq} — obstacle state at avoid-action time:")
    for r in db.execute(
        "MATCH (o:Obstacle {id: 'obs-1'}) AS OF seq $s "
        "RETURN o.distance_m AS distance, o.confidence AS confidence",
        params={"s": avoid_seq},
    ):
        print(f"  {dict(r)}")

    print(f"\nAS OF seq {avoid_seq - 1} — one tick before the avoid-action:")
    for r in db.execute(
        "MATCH (o:Obstacle {id: 'obs-1'}) AS OF seq $s "
        "RETURN o.distance_m AS distance, o.confidence AS confidence",
        params={"s": avoid_seq - 1},
    ):
        print(f"  {dict(r)}")

    print("\nObservation: at seq 5 (avoid-action moment) the controller saw")
    print("distance=3.1m, confidence=0.93 — high-confidence imminent obstacle.")
    print("One tick earlier (seq 4) it saw 3.1m / 0.81 — same distance, lower")
    print("confidence. Useful for tuning: 'what confidence threshold should fire?'")

    db.close()
    shutil.rmtree(data_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
