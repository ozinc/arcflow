"""Count(*) against a virtual label backed by a Lakehouse partition.

Plan: zero range fetches. Result: sum of per-row-group num_rows
across the parquet footer. No column chunk bytes leave object storage.

Run after 00-make-sample.py:
    python 01-count.py
"""

import os

import arcflow


def main() -> None:
    # Point the engine at the partition root. `lake://` URIs resolve
    # against this prefix at scan time.
    os.environ["OZ_LAKE_ROOT"] = os.path.abspath("./data/lake")

    # Open (or create) a workspace. The workspace holds the typed
    # catalog entry; row data stays in the Lakehouse partitions.
    db = arcflow.ArcFlow("./workspace")

    # Register the virtual label. The placeholder pattern
    # `{season}/{week}` is the Hive-partition shape; the catalog
    # records it and the planner expands it at query time.
    db.register_virtual_partition(
        label="Frame",
        partition="lake://nfl/tracks/{season}/{week}",
    )

    # Count(*) — the footer-only fast path. Sub-second wall time
    # regardless of partition size; the engine never materialises a
    # single row.
    result = db.execute("MATCH (f:Frame) RETURN count(f) AS n")
    print(result)

    db.close()


if __name__ == "__main__":
    main()
