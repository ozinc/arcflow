"""Synthesize the sample Parquet file used by subsequent steps.

Shape: per-frame (x, y) for each player, per play, per game — the
canonical multi-entity tracking layout. Deterministic — same input
seed produces byte-equal Parquet output, so CI snapshots stay stable.

Output:
    data/sample.parquet  (~50 KB)

Schema:
    game_id      str
    play_id      int64
    frame_id     int64
    timestamp    float64    seconds since play start
    player_id    str
    team         str        "home" | "away"
    x            float64    yards from goal line, [0, 120]
    y            float64    yards from sideline, [0, 53.3]
    speed        float64    yards/second
"""
from __future__ import annotations

import math
import random
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def main() -> None:
    rng = random.Random(20260430)
    out = Path(__file__).parent / "data" / "sample.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)

    games = ["G001"]
    plays = list(range(1, 6))           # 5 plays
    frames_per_play = 10                # 10 frames per play (~1 sec at 10Hz)
    frame_dt = 0.1
    home_players = [f"P{n:02d}" for n in range(1, 12)]
    away_players = [f"P{n:02d}" for n in range(12, 23)]

    rows = {
        "game_id": [],
        "play_id": [],
        "frame_id": [],
        "timestamp": [],
        "player_id": [],
        "team": [],
        "x": [],
        "y": [],
        "speed": [],
    }

    def initial_position(team: str, idx: int) -> tuple[float, float]:
        # 11 players per team in a rough line of scrimmage.
        x = 50.0 + (-2.0 if team == "home" else 2.0)
        y = 5.0 + idx * (43.3 / 11)
        return x, y

    for game_id in games:
        for play_id in plays:
            # Per-player per-play velocity vectors (yards/sec).
            velocity = {}
            for idx, pid in enumerate(home_players):
                vx = rng.gauss(2.5, 1.5)
                vy = rng.gauss(0.0, 1.0)
                velocity[("home", pid)] = (vx, vy, *initial_position("home", idx))
            for idx, pid in enumerate(away_players):
                vx = rng.gauss(-2.5, 1.5)
                vy = rng.gauss(0.0, 1.0)
                velocity[("away", pid)] = (vx, vy, *initial_position("away", idx))

            for frame_id in range(frames_per_play):
                t = frame_id * frame_dt
                for (team, pid), (vx, vy, x0, y0) in velocity.items():
                    # Add small per-frame noise so the dataset isn't perfectly
                    # linear (closer to real tracking output).
                    nx = rng.gauss(0.0, 0.05)
                    ny = rng.gauss(0.0, 0.05)
                    x = max(0.0, min(120.0, x0 + vx * t + nx))
                    y = max(0.0, min(53.3, y0 + vy * t + ny))
                    speed = math.hypot(vx, vy)

                    rows["game_id"].append(game_id)
                    rows["play_id"].append(play_id)
                    rows["frame_id"].append(frame_id)
                    rows["timestamp"].append(round(t, 4))
                    rows["player_id"].append(pid)
                    rows["team"].append(team)
                    rows["x"].append(round(x, 4))
                    rows["y"].append(round(y, 4))
                    rows["speed"].append(round(speed, 4))

    table = pa.table(
        rows,
        schema=pa.schema(
            [
                ("game_id", pa.string()),
                ("play_id", pa.int64()),
                ("frame_id", pa.int64()),
                ("timestamp", pa.float64()),
                ("player_id", pa.string()),
                ("team", pa.string()),
                ("x", pa.float64()),
                ("y", pa.float64()),
                ("speed", pa.float64()),
            ]
        ),
    )

    pq.write_table(table, out, compression="snappy")
    size_kb = out.stat().st_size / 1024
    print(f"wrote {out} ({len(rows['game_id'])} rows, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
