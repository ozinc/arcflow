"""Step 04 — Temporal queries on the loaded graph.

Demonstrates:
  - Per-player trajectory ordered by frame
  - Per-frame snapshot ("everyone at frame 4 of play 2")
  - Per-player frame counts per play (a stand-in for trajectory length
    given the WorldCypher subset shipped in 1.6.6)

Run:
    uv run python 04-temporal-queries.py
"""
from __future__ import annotations

from _load import load


def main() -> None:
    db, _ = load()

    # 1. Per-player trajectory for play 1, player P01.
    print("\n[1] Player P01 trajectory in play 1:")
    result = db.execute(
        "MATCH (p:Player {player_id: 'P01'})-[r:OBSERVED_AT]->(f:Frame) "
        "WHERE f.play_id = 1 "
        "RETURN f.frame_id AS frame, r.x AS x, r.y AS y, r.speed AS speed "
        "ORDER BY f.frame_id"
    )
    print(f"  rows: {result.row_count}")
    for row in result:
        print(
            f"    frame={row['frame']:>2}  "
            f"x={float(row['x']):6.2f}  "
            f"y={float(row['y']):5.2f}  "
            f"speed={float(row['speed']):5.2f}"
        )

    # 2. Per-frame snapshot.
    print("\n[2] Everyone at play 2, frame 4 (sorted by x):")
    result = db.execute(
        "MATCH (p:Player)-[r:OBSERVED_AT]->(f:Frame) "
        "WHERE f.play_id = 2 AND f.frame_id = 4 "
        "RETURN p.player_id AS player, p.team AS team, "
        "       r.x AS x, r.y AS y "
        "ORDER BY r.x "
        "LIMIT 5"
    )
    print(f"  rows: {result.row_count}  (showing first 5)")
    for row in result:
        print(
            f"    {row['player']}  ({row['team']})  "
            f"x={float(row['x']):6.2f}  y={float(row['y']):5.2f}"
        )

    # 3. Per-player frame count per play.
    print("\n[3] Frame count per player per play (top 5):")
    result = db.execute(
        "MATCH (p:Player)-[r:OBSERVED_AT]->(f:Frame) "
        "RETURN p.player_id AS player, f.play_id AS play, count(r) AS frames "
        "ORDER BY frames DESC, player, play "
        "LIMIT 5"
    )
    for row in result:
        print(
            f"    {row['player']}  play {row['play']}  "
            f"frames={row['frames']}"
        )

    db.close()
    print("\nOK")


if __name__ == "__main__":
    main()
