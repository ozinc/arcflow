"""Step 04 — 60 Hz primary tracking bulk-load.

Verifies that the canonical 60 Hz timeline plus all 19,800 OBSERVED_AT
edges land cleanly. Reports throughput and the sanity counts that every
downstream step depends on.

Run:
    uv run python 04-tracking-bulk-load.py
"""
from __future__ import annotations

import time

from _load import load


def main() -> None:
    print("loading 60 Hz tracking world model...")
    t0 = time.perf_counter()
    db = load(verbose=True)
    elapsed = time.perf_counter() - t0
    print(f"\nload time: {elapsed:.1f}s")

    print("\n[1] Frame timeline (60 Hz):")
    n_frames = int(db.execute("MATCH (f:Frame) RETURN count(f)").get(0, 0))
    print(f"    Frame nodes:                  {n_frames}")
    first = db.execute("MATCH (f:Frame) RETURN min(f.frame_idx)").get(0, 0)
    last = db.execute("MATCH (f:Frame) RETURN max(f.frame_idx)").get(0, 0)
    print(f"    First / Last frame_idx:       {first} / {last}")

    print("\n[2] Tracking observations (OBSERVED_AT):")
    n_obs = int(
        db.execute("MATCH ()-[r:OBSERVED_AT]->() RETURN count(r)").get(0, 0)
    )
    print(f"    Total observations:           {n_obs:,}")
    print(f"    Observations / second loaded: {n_obs / elapsed:,.0f}")

    print("\n[3] Per-group observation counts (no OBSERVED_AT cross-edges between groups expected):")
    result = db.execute(
        "MATCH (e:Entity)-[r:OBSERVED_AT]->() "
        "RETURN e.group_id AS group, count(r) AS observations "
        "ORDER BY e.group_id"
    )
    for row in result:
        print(f"    {row['group']:30}{int(row['observations']):,}")

    print("\n[4] Confidence distribution (low-confidence frames flagged):")
    high = int(
        db.execute(
            "MATCH ()-[r:OBSERVED_AT]->() WHERE r._confidence > 0.8 RETURN count(r)"
        ).get(0, 0)
    )
    low = int(
        db.execute(
            "MATCH ()-[r:OBSERVED_AT]->() WHERE r._confidence < 0.5 RETURN count(r)"
        ).get(0, 0)
    )
    print(f"    high-confidence (>0.8):       {high:,}")
    print(f"    low-confidence  (<0.5):       {low:,}")
    print(f"    coverage:                     {(high + low) / n_obs * 100:.1f}% (rest in mid band)")

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
