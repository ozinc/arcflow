"""Synthesise a tiny Hive-partitioned Parquet tree so the recipe runs
without external data. Three partitions × ~3.3k rows each.

Run once:
    python 00-make-sample.py

Generates:
    ./data/lake/nfl/tracks/season=2024/week=01/frames.parquet
    ./data/lake/nfl/tracks/season=2024/week=02/frames.parquet
    ./data/lake/nfl/tracks/season=2025/week=01/frames.parquet

Total rows: ~10,000. The schema mimics NFL Next Gen Stats tracking
data shape (frame_id, player_id, x, y, time_ms) — but at toy scale.
The point is the *path*, not the data volume; the real-world proof
point is the 311M-row partition described in the README.
"""

from pathlib import Path
import random

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path("./data/lake/nfl/tracks")
PARTITIONS = [
    ("season=2024", "week=01", 3334),
    ("season=2024", "week=02", 3333),
    ("season=2025", "week=01", 3333),
]


def synth(season_dir: str, week_dir: str, n_rows: int) -> pa.Table:
    rng = random.Random(f"{season_dir}-{week_dir}")
    return pa.table({
        "frame_id":  pa.array([i for i in range(n_rows)], type=pa.int64()),
        "player_id": pa.array([rng.randint(1, 22) for _ in range(n_rows)], type=pa.int32()),
        "x":         pa.array([round(rng.uniform(0.0, 120.0), 2) for _ in range(n_rows)], type=pa.float64()),
        "y":         pa.array([round(rng.uniform(0.0, 53.3), 2) for _ in range(n_rows)], type=pa.float64()),
        "time_ms":   pa.array([i * 100 for i in range(n_rows)], type=pa.int64()),
    })


def main() -> None:
    total = 0
    for season_dir, week_dir, n_rows in PARTITIONS:
        out = ROOT / season_dir / week_dir / "frames.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(synth(season_dir, week_dir, n_rows), out)
        print(f"  wrote {n_rows:>6,} rows → {out}")
        total += n_rows
    print(f"\nTotal rows across {len(PARTITIONS)} partitions: {total:,}")
    print("\nNext: python 01-count.py")


if __name__ == "__main__":
    main()
