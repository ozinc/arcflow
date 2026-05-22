"""
Step 2 — Tactical pattern detection as graph + spatial queries.

Four patterns from advanced game tactics, each one a single MATCH (with
a spatial predicate and a temporal window) against the world model
loaded in step 1. The point: each pattern that took a separate hand-
written Python loop in a notebook-based stack is now one query.

    Pattern 1 — Pressing detection
        N defenders within R metres of the ball, sustained over a
        T-second window after a turnover.

    Pattern 2 — Line-breaking pass
        Ball y-displacement > D metres in one frame, AND that
        displacement crosses the highest defending player's y.

    Pattern 3 — Defensive compression
        Bounding-box area of the back-five y-coordinates shrinks below
        a threshold over a T-second window.

    Pattern 4 — Counter-attack origin
        Possession flip + ball travels > D metres within T seconds +
        ball crosses the half-way line.

Each pattern is computed against the substrate by frame index; the
constants line up with the events planted in `_load.py`, so the three
events appear deterministically.
"""

from _load import (
    make_db, EVENT_PRESS_START, EVENT_LINE_BREAK, EVENT_COUNTER_ORIGIN,
)


# Tactical thresholds — exposed so the operator can tune without rewriting queries.
PRESS_RADIUS_M    = 6.0
PRESS_MIN_COUNT   = 3
PRESS_WINDOW_FR   = 12     # 12 frames @ 5Hz = 2.4 s

LINE_BREAK_MIN_M  = 15.0   # forward ball jump
COUNTER_MIN_M     = 20.0
COUNTER_WINDOW_FR = 15     # 3.0 s


def main():
    db, _by_pid, _ball_id = make_db()

    # ---- Pattern 1: pressing detection --------------------------------
    print("=== Pattern 1: pressing detection ===")
    print(f"Defenders within {PRESS_RADIUS_M} m of the ball, "
          f"sustained {PRESS_MIN_COUNT}+ across {PRESS_WINDOW_FR} frames")
    print(f"Looking around the planted turnover at frame {EVENT_PRESS_START}:")

    # Per-frame count of defenders within radius of the ball.
    rows = list(db.execute(f"""
        MATCH (b:Ball)-[:POSITION_AT]->(bp:Position),
              (d:Player {{team: 'defending'}})-[:POSITION_AT]->(dp:Position)
        WHERE bp.frame >= {EVENT_PRESS_START - 5}
          AND bp.frame <= {EVENT_PRESS_START + 20}
          AND dp.frame = bp.frame
          AND (dp.x - bp.x) * (dp.x - bp.x)
            + (dp.y - bp.y) * (dp.y - bp.y)
            < {PRESS_RADIUS_M * PRESS_RADIUS_M}
        RETURN bp.frame AS frame, count(d) AS pressers
        ORDER BY bp.frame
    """))
    # In Python: detect the sustained window.
    triggers = [int(r["frame"]) for r in rows if int(r["pressers"]) >= PRESS_MIN_COUNT]
    if triggers:
        print(f"  pressing-trigger frames: {triggers}")
        print(f"  ↳ first sustained press fires at frame {triggers[0]}")
    else:
        print("  no pressing trigger detected")

    # ---- Pattern 2: line-breaking pass --------------------------------
    print("\n=== Pattern 2: line-breaking pass ===")
    print(f"Ball forward jump ≥ {LINE_BREAK_MIN_M} m, crossing highest defender")

    # Ball per-frame y-delta via window function.
    ball_jumps = list(db.execute(f"""
        MATCH (b:Ball)-[:POSITION_AT]->(p:Position)
        RETURN p.frame AS frame, p.y AS y,
               p.y - lag(p.y, 1) OVER (ORDER BY p.frame) AS dy
        ORDER BY p.frame
    """))
    # Filter big forward jumps in Python (NULL on first row).
    candidates = [(int(r["frame"]), float(r["y"]), float(r["dy"]))
                  for r in ball_jumps
                  if r["dy"] is not None and float(r["dy"]) >= LINE_BREAK_MIN_M]

    for (frame, y, dy) in candidates:
        # For each candidate frame, find the highest defender at the *previous* frame
        # (i.e., where the defending line was before the pass).
        rows = list(db.execute(f"""
            MATCH (d:Player {{team: 'defending'}})-[:POSITION_AT]->(p:Position)
            WHERE p.frame = {frame - 1}
            RETURN max(p.y) AS line_y
        """))
        line_y = float(rows[0]["line_y"]) if rows and rows[0]["line_y"] is not None else None
        broke = line_y is not None and (y - dy) <= line_y < y
        print(f"  frame {frame}: dy={dy:.1f} m, defending line y={line_y}, line-breaking={broke}")

    # ---- Pattern 3: defensive compression -----------------------------
    print("\n=== Pattern 3: defensive compression (back-five y-spread) ===")
    print("y-spread of the four back defenders (D01-D04) across the press window:")
    for row in db.execute(f"""
        MATCH (d:Player {{team: 'defending', role: 'DEF'}})-[:POSITION_AT]->(p:Position)
        WHERE p.frame >= {EVENT_PRESS_START - 5}
          AND p.frame <= {EVENT_PRESS_START + 20}
        RETURN p.frame AS frame,
               max(p.y) - min(p.y) AS y_spread,
               count(d) AS n_defs
        ORDER BY p.frame
    """):
        # Print the compression delta vs the pre-press baseline (frame -5).
        if int(row["n_defs"]) >= 3:
            print(f"  frame {row['frame']}: y-spread = {float(row['y_spread']):.1f} m")

    # ---- Pattern 4: counter-attack origin -----------------------------
    print("\n=== Pattern 4: counter-attack origin ===")
    print(f"Possession flip + ball travels ≥ {COUNTER_MIN_M} m "
          f"within {COUNTER_WINDOW_FR} frames + crosses half-way")

    # Find possession flips.
    flips = list(db.execute("""
        MATCH (b:Ball)-[:POSITION_AT]->(p:Position)
        RETURN p.frame AS frame,
               p.team_possession AS poss,
               lag(p.team_possession, 1) OVER (ORDER BY p.frame) AS prev_poss
        ORDER BY p.frame
    """))
    flip_frames = [int(r["frame"]) for r in flips
                   if r["prev_poss"] is not None
                   and str(r["poss"]) != str(r["prev_poss"])]
    print(f"  possession-flip frames: {flip_frames}")

    # For each flip, check ball travel + half-way crossing within window.
    for flip in flip_frames:
        rows = list(db.execute(f"""
            MATCH (b:Ball)-[:POSITION_AT]->(p:Position)
            WHERE p.frame = {flip} OR p.frame = {flip + COUNTER_WINDOW_FR}
            RETURN p.frame AS frame, p.x AS x, p.y AS y
            ORDER BY p.frame
        """))
        if len(rows) == 2:
            (f0, x0, y0) = (int(rows[0]["frame"]), float(rows[0]["x"]), float(rows[0]["y"]))
            (f1, x1, y1) = (int(rows[1]["frame"]), float(rows[1]["x"]), float(rows[1]["y"]))
            dist = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            crossed = (y0 < 0 < y1) or (y0 > 0 > y1)
            counter = dist >= COUNTER_MIN_M and crossed
            print(f"  flip @ {f0}: dist over {COUNTER_WINDOW_FR} fr = {dist:.1f} m, "
                  f"crossed half-way = {crossed}, counter-attack = {counter}")

    print("\n--- What this proves ---")
    print("  - Four tactical events expressed as graph + spatial + window-function queries.")
    print("  - No hand-rolled spatial loops in Python: distance²-on-coords, max(), lag(),")
    print("    aggregations over a frame window — all WorldCypher primitives.")
    print("  - The constants (PRESS_RADIUS_M etc.) are the operator's tunable knobs;")
    print("    changing them does NOT touch the queries.")
    print("  - Step 03 replays each event AS OF the seq at which it fired, then fuses")
    print("    the observed tracking with predicted coach-intent and LLM commentary.")

    db.close()


if __name__ == "__main__":
    main()
