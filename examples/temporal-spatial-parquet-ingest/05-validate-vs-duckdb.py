"""Step 05 — Validate ArcFlow aggregates against DuckDB on the same Parquet.

This step is the load-bearing CI invariant. If ArcFlow and DuckDB disagree
on basic counts and aggregates over the same input rows, something is wrong —
probably in the recipe, possibly in the engine. Either way, CI catches it
before the recipe ships.

Run:
    uv run python 05-validate-vs-duckdb.py
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from _load import load

HERE = Path(__file__).parent
INPUT = HERE / "data" / "sample.parquet"


def main() -> None:
    if not INPUT.exists():
        raise SystemExit(
            f"Missing {INPUT}. Run 00-make-sample.py first."
        )

    # ── DuckDB side ────────────────────────────────────────────────────────
    con = duckdb.connect(":memory:")
    con.execute(f"CREATE VIEW src AS SELECT * FROM read_parquet('{INPUT}')")

    duckdb_total = con.execute("SELECT count(*) FROM src").fetchone()[0]
    duckdb_players = con.execute(
        "SELECT count(DISTINCT player_id) FROM src"
    ).fetchone()[0]
    duckdb_frames = con.execute(
        "SELECT count(DISTINCT (game_id, play_id, frame_id)) FROM src"
    ).fetchone()[0]
    duckdb_per_team = dict(
        con.execute(
            "SELECT team, count(*) FROM src GROUP BY team ORDER BY team"
        ).fetchall()
    )

    # ── ArcFlow side ──────────────────────────────────────────────────────
    db, _ = load()
    af_total = int(
        db.execute("MATCH ()-[r:OBSERVED_AT]->() RETURN count(r)").get(0, 0)
    )
    af_players = int(db.execute("MATCH (p:Player) RETURN count(p)").get(0, 0))
    af_frames = int(db.execute("MATCH (f:Frame) RETURN count(f)").get(0, 0))

    af_per_team_result = db.execute(
        "MATCH (p:Player)-[r:OBSERVED_AT]->() "
        "RETURN p.team AS team, count(r) AS n "
        "ORDER BY p.team"
    )
    af_per_team = {row["team"]: int(row["n"]) for row in af_per_team_result}
    db.close()

    # ── Compare ───────────────────────────────────────────────────────────
    failures = []
    if af_total != duckdb_total:
        failures.append(
            f"row count mismatch: arcflow={af_total} duckdb={duckdb_total}"
        )
    if af_players != duckdb_players:
        failures.append(
            f"player count mismatch: arcflow={af_players} "
            f"duckdb={duckdb_players}"
        )
    if af_frames != duckdb_frames:
        failures.append(
            f"frame count mismatch: arcflow={af_frames} duckdb={duckdb_frames}"
        )
    for team, n in duckdb_per_team.items():
        if af_per_team.get(team) != n:
            failures.append(
                f"per-team count mismatch for {team}: "
                f"arcflow={af_per_team.get(team)} duckdb={n}"
            )

    print("counts:")
    print(f"  rows           — arcflow {af_total:>5}  duckdb {duckdb_total:>5}")
    print(f"  players        — arcflow {af_players:>5}  duckdb {duckdb_players:>5}")
    print(f"  frames         — arcflow {af_frames:>5}  duckdb {duckdb_frames:>5}")
    print(f"  team-home rows — arcflow {af_per_team.get('home', 0):>5}  "
          f"duckdb {duckdb_per_team.get('home', 0):>5}")
    print(f"  team-away rows — arcflow {af_per_team.get('away', 0):>5}  "
          f"duckdb {duckdb_per_team.get('away', 0):>5}")

    if failures:
        print("\nFAIL:")
        for f in failures:
            print(f"  ✗ {f}")
        raise SystemExit(1)

    print("\nOK — ArcFlow and DuckDB agree on every aggregate.")


if __name__ == "__main__":
    main()
