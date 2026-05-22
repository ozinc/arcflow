"""Step 02 — Declare a virtual label with COMPUTE-derived properties.

Extends the registration shape from 01-register.py with a `COMPUTE`
clause. The Smart Reader evaluates the expressions at row-decode time
against the decoded RecordBatch; the values surface in `Node.properties`
alongside the parquet-resident columns; predicates on them push down
through the planner. Row data on disk is unchanged.

After this step:
- A second virtual label `TelemetryDerived` is bound to the same
  partition pattern as `TelemetrySample`, plus two derived properties:
    temp_f          = temp_c * 9 / 5 + 32
    temp_dewpoint   = temp_c - ((100 - humidity) / 5)
- A `ComputedColumn` entry lands in the catalog manifest alongside
  the `VirtualLabelEntry` (same atomic two-file commit; monotonic
  epoch).
- A predicate-pushed query against `t.temp_dewpoint < 10` runs the
  expression only on row groups whose `temp_c` + `humidity` statistics
  could possibly produce a sub-10 result.

Run:
    uv run python 02-compute.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if not Path("data/lake/telemetry").exists():
    print(
        "data/lake/telemetry is missing — run `python 00-make-sample.py` first.",
        file=sys.stderr,
    )
    sys.exit(1)


def main() -> None:
    from arcflow import ArcFlow

    workspace = Path("data/workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    db = ArcFlow(str(workspace))

    # ── Register the COMPUTE-extended virtual label ──
    #
    # Same DDL as 01-register.py, plus a COMPUTE clause that declares
    # two derived properties. Names become first-class property keys on
    # the virtual label — indistinguishable from parquet-resident
    # columns at the Cypher surface.
    db.execute(
        "CREATE NODE LABEL TelemetryDerived ("
        "  ts        TIMESTAMP,"
        "  sensor_id STRING,"
        "  temp_c    DOUBLE,"
        "  humidity  DOUBLE"
        ") VIRTUAL FROM PARTITION "
        "'lake://local/telemetry/{year}/{month}/{day}/{sensor}'"
        "COMPUTE"
        "  temp_f        = temp_c * 9 / 5 + 32,"
        "  temp_dewpoint = temp_c - ((100 - humidity) / 5)"
    )
    print("registered — TelemetryDerived (with COMPUTE)")

    # ── Inspect the catalog manifest ──
    #
    # The manifest carries a ComputedColumn entry per declared derived
    # column: name, return_type, dependency list (which parquet columns
    # + partition keys + earlier computed columns it references), and
    # the Arrow-compatible expression IR.
    manifest_dir = workspace / "canonical"
    manifest_files = sorted(manifest_dir.glob("manifest_*.json"))
    if manifest_files:
        latest = manifest_files[-1]
        payload = json.loads(latest.read_text())
        for entry in payload.get("virtual_labels", []):
            if entry.get("label") != "TelemetryDerived":
                continue
            computed = entry.get("computed_columns", [])
            print(f"\nmanifest: {latest.name}")
            print(f"  TelemetryDerived.computed_columns: {len(computed)}")
            for c in computed:
                deps = ", ".join(c.get("dependencies", []))
                print(f"    - {c.get('name')!r:18} : {c.get('return_type')!r:10} ← {deps}")

    # ── Query against a computed column ──
    #
    # `WHERE t.temp_dewpoint < 10.0` is pushable when the substrate has
    # enough column stats on the inputs (temp_c, humidity) to prove a
    # row group can be skipped before evaluating the expression.
    # Partition + row-group pruning collapses the candidate set first;
    # per-row arithmetic runs only on what survives.
    result = db.execute(
        "MATCH (t:TelemetryDerived) "
        "WHERE t.year = 2026 AND t.month = 3 "
        "  AND t.temp_dewpoint < 10.0 "
        "RETURN t.sensor_id, t.temp_c, t.humidity, t.temp_dewpoint "
        "ORDER BY t.temp_dewpoint LIMIT 5"
    )
    print("\nlow-dewpoint rows (computed at scan time):")
    for row in result:
        print(
            f"  sensor={row['sensor_id']:>10}  "
            f"temp_c={row['temp_c']:.2f}  "
            f"humidity={row['humidity']:.1f}  "
            f"dewpoint={row['temp_dewpoint']:.2f}"
        )

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
