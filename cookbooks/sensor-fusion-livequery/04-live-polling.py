"""Step 04 — Live-polling pattern with a sliding window.

Simulates a sensor stream by loading the graph progressively, frame by
frame. After each frame is appended the same trust-weighted standing
query is re-executed against the always-current graph. The query asks
about the *recent past* (the last WINDOW frames), not the all-time mean —
that is what a live-monitoring system actually wants.

This is the recipe for live queries against the shipped 1.6.6 surface:
the agent re-runs `execute()` after each event ingest. The query is the
contract; the polling cadence and window are the agent's choice.

Run:
    uv run python 04-live-polling.py
"""
from __future__ import annotations

from _load import load

TRUST_FLOOR = 0.7
TEMP_ALERT = 60.0
WINDOW = 10           # frames — the standing query looks back this far


def windowed_trust_temp(
    db, robot_id: str, frame_lo: int, frame_hi: int
) -> tuple[float, int]:
    """Confidence-weighted mean temperature for one robot over a frame window."""
    result = db.execute(
        "MATCH (s:Sensor)-[r:READ]->(f:Frame) "
        f"WHERE s.modality = 'temperature' AND s.robot_id = '{robot_id}' "
        f"AND r.confidence > {TRUST_FLOOR} "
        f"AND f.frame_id >= {frame_lo} AND f.frame_id <= {frame_hi} "
        "RETURN r.value AS value, r.confidence AS conf"
    )
    sv = sc = 0.0
    n = 0
    for row in result:
        v = float(row["value"])
        c = float(row["conf"])
        sv += v * c
        sc += c
        n += 1
    return (sv / sc if sc > 0 else 0.0, n)


def main() -> None:
    print(f"simulating live sensor stream — sliding window = last {WINDOW} frames\n")
    print(
        f"{'now':>5}  {'R01 temp':>10}  {'R02 temp':>10}  {'R03 temp':>10}  alerts"
    )

    last_alerts: set[str] = set()
    poll_at = [10, 30, 50, 60, 65, 70, 75, 80, 99]
    for now in poll_at:
        db, _ = load(max_frame=now)
        lo = max(0, now - WINDOW + 1)
        line = [f"{now:>5}"]
        active: set[str] = set()
        for rid in ("R01", "R02", "R03"):
            wmean, _ = windowed_trust_temp(db, rid, lo, now)
            line.append(f"{wmean:>9.2f}°C")
            if wmean > TEMP_ALERT:
                active.add(rid)
        new_alerts = active - last_alerts
        cleared = last_alerts - active
        annot = []
        if new_alerts:
            annot.append("FIRE: " + ",".join(sorted(new_alerts)))
        if cleared:
            annot.append("CLEAR: " + ",".join(sorted(cleared)))
        line.append("  ".join(annot) if annot else "")
        print("  ".join(line))
        last_alerts = active
        db.close()

    print("\nOK")


if __name__ == "__main__":
    main()
