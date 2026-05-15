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
is the next wave of substrate work; until it lands, queries against
virtual labels return `QueryError::VirtualLabelNotYetQueryable`. The
registration path itself is real-bytes-on-disk now.

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

    # ── What would happen on query (target end-state) ──
    #
    # `MATCH (t:TelemetrySample) WHERE t.temp_c > 25.0 RETURN count(t)`
    # — once the planner-side rewriter is wired through, this rewrites
    # to a manifest-pruned, predicate-pushed Parquet scan. Today it
    # returns QueryError::VirtualLabelNotYetQueryable; the cookbook
    # documents the target shape so consumers know what to expect.
    print("\nnext wave: planner-side rewriter — `MATCH (:TelemetrySample)`")
    print("           is currently `QueryError::VirtualLabelNotYetQueryable`")

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
