"""Same query, two deadlines. Demonstrates the divergence between
`transport_outcome = 'complete'` (deadline ample, full result) and
`'truncated'` (deadline tight, what-was-reachable result).

Run after 00-make-sample.py:
    python 01-deadline.py
"""

import os
import time

import arcflow


def report(label: str, t0: float, result) -> None:
    wall_ms = (time.perf_counter() - t0) * 1000.0
    print(f"=== {label} ===")
    print(f"  rows returned:       {len(result.rows):>10,}")
    print(f"  transport_outcome:   {result.transport_outcome}")
    if result.io_stats is not None:
        print(f"  io_stats.bytes_read: {result.io_stats.bytes_read:>10,}")
        print(f"  io_stats.lane_used:  {result.io_stats.lane_used}")
    print(f"  wall time:           {wall_ms:>6.1f} ms")
    print()


def main() -> None:
    os.environ["OZ_LAKE_ROOT"] = os.path.abspath("./data/lake")

    db = arcflow.ArcFlow("./workspace")

    db.register_virtual_partition(
        label="Frame",
        partition="lake://frames/{play_id}",
    )

    # Cypher query — same in both runs. The planner reads x, y, frame_id
    # via column projection; the `blob` column stays on disk.
    cypher = "MATCH (f:Frame) WHERE f.x > 50.0 RETURN f.frame_id, f.x, f.y"

    # Run 1: generous deadline — query completes
    t0 = time.perf_counter()
    result_complete = db.execute(
        cypher,
        options=arcflow.QueryOptions(deadline_ms=5000),
    )
    report("Generous deadline (5000 ms)", t0, result_complete)

    # Run 2: tight deadline — query truncates
    # 10 ms is well below the full read time on the 5-partition sample;
    # the engine returns what it has accumulated so far.
    t0 = time.perf_counter()
    result_truncated = db.execute(
        cypher,
        options=arcflow.QueryOptions(deadline_ms=10),
    )
    report("Tight deadline (10 ms)", t0, result_truncated)

    # The two results answer the same Cypher pattern. The first is
    # complete; the second is what was reachable in 10 ms. Both are
    # deterministic for a snapshot — re-running 01-deadline.py against
    # the same workspace + same partition layout produces the same
    # row counts.

    db.close()


if __name__ == "__main__":
    main()
