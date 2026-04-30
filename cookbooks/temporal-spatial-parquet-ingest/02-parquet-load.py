"""Step 02 — Load data/sample.parquet into ArcFlow.

Reads the synthesized Parquet, deduplicates Player and Frame keys, then
emits one CREATE per node and one CREATE per OBSERVED_AT edge. Runs
in-memory for fast iteration; the load function is shared with subsequent
steps via _load.py.

This step demonstrates the canonical "Parquet → ArcFlow batch ingest"
pattern. For larger datasets (≥ 1M rows), chunk the inserts and consider
parallel batches. The shape stays the same.

Run:
    uv run python 02-parquet-load.py
"""
from __future__ import annotations

import time

from _load import load


def main() -> None:
    t0 = time.perf_counter()
    db, rows = load(verbose=True)
    elapsed = time.perf_counter() - t0
    print(f"loaded in {elapsed:.2f}s ({len(rows) / elapsed:.0f} rows/sec)")

    n_players = db.execute("MATCH (p:Player) RETURN count(p)").get(0, 0)
    n_frames = db.execute("MATCH (f:Frame) RETURN count(f)").get(0, 0)
    n_edges = db.execute(
        "MATCH ()-[r:OBSERVED_AT]->() RETURN count(r)"
    ).get(0, 0)

    print(f"in-graph: players={n_players}, frames={n_frames}, edges={n_edges}")
    db.close()
    print("OK")


if __name__ == "__main__":
    main()
