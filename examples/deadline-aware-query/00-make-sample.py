"""Synthesise a Hive-partitioned Parquet tree wide enough that a tight
deadline can demonstrably truncate. Five partitions × ~10k rows each
= ~50k rows total. One column carries varied compression density so
some range fetches are noticeably slower than others.

Run once:
    python 00-make-sample.py

Generates:
    ./data/lake/frames/play_id=1000/frames.parquet
    ./data/lake/frames/play_id=1024/frames.parquet
    ./data/lake/frames/play_id=2048/frames.parquet
    ./data/lake/frames/play_id=4096/frames.parquet
    ./data/lake/frames/play_id=8192/frames.parquet

Schema mimics a sports-tracking shape (frame_id, play_id, x, y,
time_ms, blob) — `blob` is a noisy column that exists to make some
reads non-trivial in wall time. The recipe's 01-deadline.py reads
`x` and `y` only; `blob` stays on disk except when the deadline is
generous enough to let it land.
"""

from pathlib import Path
import os
import random

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path("./data/lake/frames")
PARTITIONS = [
    ("play_id=1000", 10_000),
    ("play_id=1024", 10_000),
    ("play_id=2048", 10_000),
    ("play_id=4096", 10_000),
    ("play_id=8192", 10_000),
]


def synth(partition_dir: str, n_rows: int) -> pa.Table:
    rng = random.Random(partition_dir)
    return pa.table({
        "frame_id":  pa.array([i for i in range(n_rows)], type=pa.int64()),
        "play_id":   pa.array([int(partition_dir.split("=")[1])] * n_rows, type=pa.int64()),
        "x":         pa.array([round(rng.uniform(0.0, 120.0), 4) for _ in range(n_rows)], type=pa.float64()),
        "y":         pa.array([round(rng.uniform(0.0, 53.3), 4) for _ in range(n_rows)], type=pa.float64()),
        "time_ms":   pa.array([i * 33 for i in range(n_rows)], type=pa.int64()),
        # `blob` is a deliberately noisy column to make some reads slower.
        # The recipe's queries don't project it; column-pruning leaves it
        # on disk under generous deadlines and tight ones alike.
        "blob":      pa.array([os.urandom(256).hex() for _ in range(n_rows)], type=pa.string()),
    })


def main() -> None:
    total = 0
    for partition_dir, n_rows in PARTITIONS:
        out = ROOT / partition_dir / "frames.parquet"
        out.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(synth(partition_dir, n_rows), out, compression="zstd")
        print(f"  wrote {n_rows:>6,} rows → {out}")
        total += n_rows
    print(f"\nTotal rows across {len(PARTITIONS)} partitions: {total:,}")
    print("\nNext: python 01-deadline.py")


if __name__ == "__main__":
    main()
