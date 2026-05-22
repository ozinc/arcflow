"""Step 01 — Register a virtual label against the Hive-partitioned tree.

Demonstrates the two registration paths — DDL through Cypher and the
direct Python FFI — and inspects the resulting catalog manifest. The
manifest commit is atomic; the manifest survives close-and-reopen of
the workspace.

After this step:
- The workspace has a virtual label `TelemetrySample` bound to the
  `data/lake/telemetry/year={year}/month={month}/day={day}/sensor={sensor}.parquet`
  partition pattern.
- A `VirtualLabelEntry` row exists in the catalog manifest.
- The manifest epoch advances; the new epoch is returned by the
  registration call.

The planner-side rewriter for `MATCH (:TelemetrySample ...)` patterns
decomposes the pattern into a manifest-pruned, predicate-pushed
Parquet scan. `count`, filter, and projection light up natively
through the substrate; row data never enters engine RAM.

Run:
    uv run python 01-register.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Run 00-make-sample.py first if the synthetic tree isn't there.
if not Path("data/lake/telemetry").exists():
    print("data/lake/telemetry is missing — run `python 00-make-sample.py` first.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    from arcflow import ArcFlow

    workspace = Path("data/workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    db = ArcFlow(str(workspace))

    # ── Path A — Cypher DDL ──
    #
    # Parses the DDL, validates the typed schema against the Parquet
    # files' schema, and commits a VirtualLabelEntry to the catalog.
    db.execute(
        "CREATE NODE LABEL TelemetrySample ("
        "  ts        TIMESTAMP,"
        "  sensor_id STRING,"
        "  temp_c    DOUBLE,"
        "  humidity  DOUBLE"
        ") VIRTUAL FROM PARTITION "
        "'lake://local/telemetry/{year}/{month}/{day}/{sensor}'"
    )
    print("registered via DDL — TelemetrySample")

    # ── Path B — Direct FFI ──
    #
    # Same shape, no Cypher round-trip. Returns the new manifest
    # epoch (monotonic int).
    epoch_b = db.register_virtual_partition(
        label="TelemetrySampleAlt",
        partition="lake://local/telemetry/{year}/{month}/{day}/{sensor}",
    )
    print(f"registered via FFI    — TelemetrySampleAlt (epoch={epoch_b})")

    # ── Inspect the catalog manifest ──
    #
    # Atomic-commit produces canonical/manifest_<epoch>.json under the
    # workspace. The CURRENT pointer is the two-rename target.
    manifest_dir = workspace / "canonical"
    manifest_files = sorted(manifest_dir.glob("manifest_*.json"))
    if not manifest_files:
        print(f"no manifest files under {manifest_dir} — expected ≥ 1 after registration")
        db.close()
        return

    latest = manifest_files[-1]
    payload = json.loads(latest.read_text())
    virtual_labels = payload.get("virtual_labels", [])
    print(f"\nmanifest: {latest.name}")
    print(f"  virtual_labels: {len(virtual_labels)}")
    for entry in virtual_labels:
        print(
            f"    - {entry.get('label')!r:24} "
            f"partition={entry.get('partition_pattern')!r:60} "
            f"resolver_kind={entry.get('resolver_kind')!r}"
        )

    # ── Query against the virtual label ──
    #
    # `MATCH (t:TelemetrySample) WHERE t.temp_c > 25.0 RETURN count(t)`
    # resolves through the planner-side rewriter: partition pruning
    # narrows the file set, row-group statistics narrow it again, the
    # column-pruned scan reads only the columns the projection asks
    # for. Row data never enters engine RAM.
    print("\nquery surface: `MATCH (:TelemetrySample)` patterns resolve")
    print("               through the predicate-pushdown rewriter; see 02-compute.py")

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
