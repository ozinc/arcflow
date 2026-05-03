"""Step 12 — Replay ingest at the source 60 Hz cadence.

The earlier steps load the world model in batch — fast, but synthetic.
The interesting case is replaying observations at the same rate the live
sensor would feed them: 60 Hz tick = 16.67 ms per Frame. At that cadence:

  - The engine's spatial index updates per-frame (~ms latency)
  - LIVE views (or polled equivalents) maintain at the source rate
  - Behavior-graph triggers fire on every Frame insert
  - Cross-stream queries reflect the latest mutation within ~20 ms

This step replays a 1-second window (60 Frames) at real-time cadence
and reports the per-tick query latency for a representative LIVE
shape (cross-group proximity within a fixed threshold).

Run:
    uv run python 12-replay-at-rate.py
"""
from __future__ import annotations

import time
from pathlib import Path

import pyarrow.parquet as pq

from arcflow import ArcFlow

DATA = Path(__file__).parent / "data" / "sample"
TICK_HZ = 60
TICK_S = 1.0 / TICK_HZ
REPLAY_FRAMES = 60  # 1 second at 60 Hz


def main() -> None:
    if not (DATA / "tracking.parquet").exists():
        raise SystemExit("Run 00-make-sample.py first.")

    rows = pq.read_table(DATA / "tracking.parquet").to_pylist()
    by_frame: dict[int, list[dict]] = {}
    for r in rows:
        by_frame.setdefault(int(r["frame_idx"]), []).append(r)

    db = ArcFlow()  # in-memory

    # Pre-create the entities + a small frame window we'll replay into
    for group in ("alpha", "beta"):
        for n in range(11):
            entity_id = f"{group}-{n:02d}"
            db.execute(
                f"CREATE (:Entity {{entity_id: '{entity_id}', group_id: '{group}'}})"
            )

    print(f"\nReplaying {REPLAY_FRAMES} frames at {TICK_HZ} Hz "
          f"(target tick = {TICK_S*1000:.2f} ms)...\n")

    insert_latencies: list[float] = []
    query_latencies: list[float] = []
    overruns = 0

    print("    frame   inserts (ms)   query (ms)   tick total   notes")
    print("    -----   ------------   ----------   ----------   -----")

    start = time.perf_counter()
    for frame_idx in range(REPLAY_FRAMES):
        tick_start = time.perf_counter()

        # Phase 1 — insert the Frame and the 22 OBSERVED_AT edges for this tick
        ti = time.perf_counter()
        t_ns = frame_idx * (10**9 // TICK_HZ)
        db.execute(
            f"CREATE (:Frame {{frame_idx: {frame_idx}, time_master_ns: {t_ns}}})"
        )
        for r in by_frame.get(frame_idx, []):
            db.execute(
                "MATCH (e:Entity {entity_id: '" + r["entity_id"] + "'}),"
                f"      (f:Frame {{frame_idx: {frame_idx}}})"
                f" CREATE (e)-[:OBSERVED_AT {{"
                f"  x: {r['x']}, y: {r['y']},"
                f"  speed: {r['speed']},"
                f"  _confidence: {r['dqi']},"
                f"  _observation_class: 'observed'"
                f"}}]->(f)"
            )
        insert_ms = (time.perf_counter() - ti) * 1000

        # Phase 2 — run the LIVE-equivalent query: cross-group proximity at this tick.
        # Two-phase: pull all 22 positions at this Frame, compute distance in Python.
        # Mirrors the pattern in 09-live-views.py.
        tq = time.perf_counter()
        result = db.execute(
            "MATCH (e:Entity)-[r:OBSERVED_AT]->(f:Frame) "
            f"WHERE f.frame_idx = {frame_idx} "
            "RETURN e.entity_id AS entity, e.group_id AS group, r.x AS x, r.y AS y"
        )
        positions = [
            (row["group"], float(row["x"]), float(row["y"]))
            for row in result
        ]
        proximity_pairs = 0
        threshold_sq = 8.0 * 8.0
        for i, (gi, xi, yi) in enumerate(positions):
            for j in range(i + 1, len(positions)):
                gj, xj, yj = positions[j]
                if gi != gj:
                    dx = xi - xj
                    dy = yi - yj
                    if dx * dx + dy * dy < threshold_sq:
                        proximity_pairs += 1
        query_ms = (time.perf_counter() - tq) * 1000

        tick_elapsed = time.perf_counter() - tick_start
        tick_ms = tick_elapsed * 1000
        notes = ""
        if tick_elapsed > TICK_S:
            overruns += 1
            notes = "OVERRUN"
        else:
            slack = (TICK_S - tick_elapsed) * 1000
            notes = f"slack={slack:.2f} ms"

        if frame_idx % 10 == 0:
            print(
                f"    {frame_idx:>5}   {insert_ms:>10.2f}    {query_ms:>8.2f}   "
                f"{tick_ms:>8.2f} ms   {notes} (pairs={proximity_pairs})"
            )

        insert_latencies.append(insert_ms)
        query_latencies.append(query_ms)

        # Sleep to maintain real-time cadence
        if tick_elapsed < TICK_S:
            time.sleep(TICK_S - tick_elapsed)

    total = time.perf_counter() - start

    def percentile(values: list[float], p: float) -> float:
        s = sorted(values)
        idx = int(len(s) * p / 100)
        return s[min(idx, len(s) - 1)]

    print("\nReplay summary:")
    print(f"    target wall-clock for {REPLAY_FRAMES} frames @ {TICK_HZ} Hz: "
          f"{REPLAY_FRAMES * TICK_S:.2f}s")
    print(f"    actual wall-clock:                                        "
          f"{total:.2f}s")
    print(f"    overruns (tick > {TICK_S*1000:.2f} ms):                          "
          f"{overruns}/{REPLAY_FRAMES}")
    print(f"    insert latency  p50 / p90 / p99: "
          f"{percentile(insert_latencies, 50):.2f} / "
          f"{percentile(insert_latencies, 90):.2f} / "
          f"{percentile(insert_latencies, 99):.2f} ms")
    print(f"    query  latency  p50 / p90 / p99: "
          f"{percentile(query_latencies, 50):.2f} / "
          f"{percentile(query_latencies, 90):.2f} / "
          f"{percentile(query_latencies, 99):.2f} ms")

    db.close()
    print("\nOK — 60 Hz replay complete.")


if __name__ == "__main__":
    main()
