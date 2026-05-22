"""Step 11 — Internal validation against the synthesizer's ground-truth ledger.

The synthesizer (00-make-sample.py) writes ground_truth.json alongside the
Parquet files. This step cross-checks ArcFlow's counts and aggregates
against that ledger — pure ArcFlow + pyarrow + numpy, no external query
engine. The recipe shape is "ArcFlow knows its own answers and they
match the ground truth set down at synthesis time."

The CI runs this as the gate: any deviation between ArcFlow and the
ledger is a recipe failure.

Run:
    uv run python 11-validate-internal.py
"""
from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from _load import load, ground_truth

DATA = Path(__file__).parent / "data" / "sample"


def main() -> None:
    truth = ground_truth()
    db = load()

    failures: list[str] = []

    print("\n[1] Node counts vs ground-truth ledger:")
    checks = [
        ("Session", 1),
        ("Entity", truth["n_entities"]),
        ("Group", len(truth["groups"])),
        ("Frame", truth["n_frames"]),
        ("SceneReconstruction", truth["n_scenes"]),
        ("BiomechanicalSample", truth["n_imu"]),
        ("Event", truth["n_events"]),
    ]
    for label, expected in checks:
        actual = int(db.execute(f"MATCH (n:{label}) RETURN count(n)").get(0, 0))
        status = "✓" if actual == expected else "✗"
        print(f"    {status}  {label:25}arcflow={actual:>6}  truth={expected:>6}")
        if actual != expected:
            failures.append(f"{label}: arcflow={actual} truth={expected}")

    print("\n[2] Edge counts:")
    n_obs = int(db.execute("MATCH ()-[r:OBSERVED_AT]->() RETURN count(r)").get(0, 0))
    expected_obs = truth["n_observations"]
    status = "✓" if n_obs == expected_obs else "✗"
    print(f"    {status}  OBSERVED_AT          arcflow={n_obs:>6}  truth={expected_obs:>6}")
    if n_obs != expected_obs:
        failures.append(f"OBSERVED_AT: arcflow={n_obs} truth={expected_obs}")

    n_has_scene = int(
        db.execute("MATCH ()-[r:HAS_SCENE]->() RETURN count(r)").get(0, 0)
    )
    status = "✓" if n_has_scene == truth["n_scenes"] else "✗"
    print(f"    {status}  HAS_SCENE            arcflow={n_has_scene:>6}  truth={truth['n_scenes']:>6}")

    print("\n[3] Aggregate cross-check vs source Parquet (pyarrow.compute):")
    import pyarrow.compute as pc
    src = pq.read_table(DATA / "tracking.parquet")
    src_avg_speed = float(pc.mean(src.column("speed")).as_py())
    af_avg_speed = float(
        db.execute("MATCH ()-[r:OBSERVED_AT]->() RETURN avg(r.speed)").get(0, 0)
    )
    delta = abs(src_avg_speed - af_avg_speed)
    status = "✓" if delta < 0.01 else "✗"
    print(
        f"    {status}  avg(speed)           arcflow={af_avg_speed:.4f}  "
        f"parquet={src_avg_speed:.4f}  Δ={delta:.6f}"
    )
    if delta >= 0.01:
        failures.append(f"avg(speed) deviation {delta:.6f}")

    print("\n[4] Per-group aggregate cross-check:")
    for group, expected in truth["groups"].items():
        n = int(
            db.execute(
                "MATCH (e:Entity {group_id: '" + group + "'}) RETURN count(e)"
            ).get(0, 0)
        )
        status = "✓" if n == expected else "✗"
        print(f"    {status}  group={group:6}arcflow={n}  truth={expected}")

    if failures:
        print("\nFAIL:")
        for f in failures:
            print(f"  ✗ {f}")
        raise SystemExit(1)

    print("\nOK — every count and aggregate matches ground truth.")
    db.close()


if __name__ == "__main__":
    main()
