"""Shared loader used by every step that needs the graph in memory.

Each step opens a fresh in-memory ArcFlow database and re-loads from the
Parquet file. Loading 1100 rows takes ~0.1 seconds; for the recipe scale,
re-loading per step is faster than the disk round-trip would be.

For larger datasets, swap this for an ArcFlow persistent path and load once
in step 02, then read in subsequent steps. The recipe shape stays the same.
"""
from __future__ import annotations

from pathlib import Path

import pyarrow.parquet as pq

from arcflow import ArcFlow

HERE = Path(__file__).parent
INPUT = HERE / "data" / "sample.parquet"


def load(verbose: bool = False) -> tuple[ArcFlow, list[dict]]:
    """Load sample.parquet into a fresh in-memory ArcFlow. Returns (db, rows)."""
    if not INPUT.exists():
        raise SystemExit(f"Missing {INPUT}. Run 00-make-sample.py first.")

    table = pq.read_table(INPUT)
    rows = table.to_pylist()

    players = {(r["player_id"], r["team"]) for r in rows}
    frames = {
        (r["game_id"], r["play_id"], r["frame_id"], r["timestamp"]) for r in rows
    }

    db = ArcFlow()  # in-memory

    for pid, team in sorted(players):
        db.execute(
            f"CREATE (:Player {{player_id: '{pid}', team: '{team}'}})"
        )

    for game_id, play_id, frame_id, ts in sorted(frames):
        db.execute(
            "CREATE (:Frame {"
            f"game_id: '{game_id}', play_id: {play_id}, "
            f"frame_id: {frame_id}, timestamp: {ts}"
            "})"
        )

    for r in rows:
        db.execute(
            "MATCH (p:Player {player_id: '" + r["player_id"] + "'}), "
            "(f:Frame {game_id: '" + r["game_id"] + "', "
            f"play_id: {r['play_id']}, frame_id: {r['frame_id']}}}) "
            "CREATE (p)-[:OBSERVED_AT {"
            f"x: {r['x']}, y: {r['y']}, speed: {r['speed']}"
            "}]->(f)"
        )

    if verbose:
        print(
            f"loaded {len(rows)} rows, {len(players)} players, "
            f"{len(frames)} frames"
        )

    return db, rows
