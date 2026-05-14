"""Step 03 — Trust-weighted aggregates and threshold alerts.

Demonstrates two complementary patterns over the same data:

  1. Filter-then-aggregate: ignore any reading whose confidence is below
     the trust floor, then take the plain mean of the survivors.

  2. Confidence-weighted aggregate: keep every reading, but weight its
     contribution by its confidence (Σ(value · conf) / Σ(conf)).

Production sensor-fusion pipelines blend both: filter out clearly-bad
frames, then weight the rest. This recipe shows each in isolation so the
behaviors are diff-able.

Run:
    uv run python 03-trust-weighted-alerts.py
"""
from __future__ import annotations

from _load import load

TRUST_FLOOR = 0.7
TEMP_ALERT = 60.0      # °C — anything above this is a thermal anomaly


def main() -> None:
    db, _ = load()

    print(f"\n[1] Plain mean temperature per robot (no confidence filter):")
    result = db.execute(
        "MATCH (s:Sensor)-[r:READ]->(:Frame) "
        "WHERE s.modality = 'temperature' "
        "RETURN s.robot_id AS robot, avg(r.value) AS mean_temp "
        "ORDER BY s.robot_id"
    )
    for row in result:
        print(f"    {row['robot']}  mean={float(row['mean_temp']):6.2f}°C")

    print(f"\n[2] Trust-floor mean (confidence > {TRUST_FLOOR}):")
    result = db.execute(
        "MATCH (s:Sensor)-[r:READ]->(:Frame) "
        f"WHERE s.modality = 'temperature' AND r.confidence > {TRUST_FLOOR} "
        "RETURN s.robot_id AS robot, avg(r.value) AS mean_temp, "
        "       count(r) AS n_kept "
        "ORDER BY s.robot_id"
    )
    for row in result:
        print(
            f"    {row['robot']}  mean={float(row['mean_temp']):6.2f}°C  "
            f"kept={row['n_kept']}"
        )

    # Confidence-weighted aggregate.
    # WorldCypher returns scalars as strings, so the per-row pairs come
    # back from one MATCH and we reduce in Python.
    print(f"\n[3] Confidence-weighted mean temperature per robot:")
    result = db.execute(
        "MATCH (s:Sensor)-[r:READ]->(:Frame) "
        "WHERE s.modality = 'temperature' "
        "RETURN s.robot_id AS robot, r.value AS value, r.confidence AS conf"
    )
    weighted: dict[str, tuple[float, float]] = {}
    for row in result:
        rid = row["robot"]
        v = float(row["value"])
        c = float(row["conf"])
        sv, sc = weighted.get(rid, (0.0, 0.0))
        weighted[rid] = (sv + v * c, sc + c)

    for rid in sorted(weighted):
        sv, sc = weighted[rid]
        wmean = sv / sc if sc > 0 else float("nan")
        flag = "  ALERT" if wmean > TEMP_ALERT else ""
        print(f"    {rid}  weighted_mean={wmean:6.2f}°C{flag}")

    print(f"\n[4] Per-frame trust-weighted temperature for R01 (alert frames):")
    # All temperature readings on R01 — sensors fuse on the shared Frame.
    result = db.execute(
        "MATCH (s:Sensor)-[r:READ]->(f:Frame) "
        "WHERE s.modality = 'temperature' AND s.robot_id = 'R01' "
        "RETURN f.frame_id AS frame, r.value AS value, r.confidence AS conf "
        "ORDER BY f.frame_id"
    )
    by_frame: dict[int, list[tuple[float, float]]] = {}
    for row in result:
        f = int(row["frame"])
        by_frame.setdefault(f, []).append(
            (float(row["value"]), float(row["conf"]))
        )

    hot = []
    for f in sorted(by_frame):
        sv = sum(v * c for v, c in by_frame[f])
        sc = sum(c for _, c in by_frame[f])
        wmean = sv / sc if sc > 0 else 0.0
        if wmean > TEMP_ALERT:
            hot.append((f, wmean))
    print(f"    {len(hot)} alerting frames out of {len(by_frame)}")
    for f, w in hot[:5]:
        print(f"      frame {f:3d}  weighted_mean={w:6.2f}°C")

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
