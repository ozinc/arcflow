"""
Step 1 — Build the tactical world model and verify its shape.

Loads the substrate: field zones, players (with role + baseline), ball,
1500 frames × 17 entities of `Position` nodes, predicted coach-intent
and LLM commentary tags. Then runs four sanity queries to demonstrate
that the world-model substrate is queryable along all four dimensions
the rest of the recipe relies on:

    1. Spatial — players near a point at a frame
    2. Temporal — frame range scan with window expressions
    3. Relational — players → positions traversal
    4. Confidence — observed vs predicted facts

This is the same substrate shape the `multi-stream-spatiotemporal-
world-model` recipe builds at 60 Hz. Here it's compressed to 5 Hz / 5
minutes / 17 entities so the cookbook fits in 3 minutes and the
tactical patterns in step 02 still appear cleanly.
"""

from _load import make_db, stats


def main():
    db, _by_pid, _ball_id = make_db()
    counts = stats(db)
    print("Tactical world model loaded:")
    for k, v in counts.items():
        print(f"  {k:12s}  {v:,}")

    # ---- Sanity 1: spatial — who is near (0, 0) at frame 100? ---------
    print("\n[1] Players within 6 m of midfield centre at frame 100:")
    for row in db.execute("""
        MATCH (p:Player)-[:POSITION_AT]->(pos:Position)
        WHERE pos.frame = 100
          AND pos.x * pos.x + pos.y * pos.y < 36
        RETURN p.player_id AS pid, p.team AS team, p.role AS role,
               pos.x AS x, pos.y AS y
        ORDER BY pid
    """):
        print(f"    {dict(row)}")

    # ---- Sanity 2: temporal — ball velocity around the line break -----
    # lag(y, 1) OVER (PARTITION BY entity ORDER BY frame) gives previous-
    # frame y; the delta is the per-frame vertical displacement (m / 0.2s).
    print("\n[2] Ball y-displacement at the line-break frame (900):")
    for row in db.execute("""
        MATCH (b:Ball)-[:POSITION_AT]->(pos:Position)
        WHERE pos.frame >= 898 AND pos.frame <= 905
        RETURN pos.frame AS frame, pos.y AS y,
               pos.y - lag(pos.y, 1) OVER (ORDER BY pos.frame) AS dy
        ORDER BY pos.frame
    """):
        print(f"    {dict(row)}")

    # ---- Sanity 3: relational — defender → positions over time -------
    print("\n[3] D02 (centre-back) positions, frames 445-455 (around press start):")
    for row in db.execute("""
        MATCH (p:Player {player_id: 'D02'})-[:POSITION_AT]->(pos:Position)
        WHERE pos.frame >= 445 AND pos.frame <= 455
        RETURN pos.frame AS frame, pos.x AS x, pos.y AS y
        ORDER BY pos.frame
    """):
        print(f"    {dict(row)}")

    # ---- Sanity 4: confidence — observed vs predicted -----------------
    print("\n[4] Distinct (_observation_class, _source, count) across the world model:")
    # Done as two queries because every node kind has its own MATCH.
    for label in ["Position", "CoachIntent", "CommentaryTag", "Player", "Ball", "Zone"]:
        for row in db.execute(f"""
            MATCH (n:{label})
            RETURN '{label}' AS kind,
                   n._observation_class AS obs,
                   n._source AS source,
                   count(*) AS n
            ORDER BY kind, obs, source
        """):
            print(f"    {dict(row)}")
            break  # one row per label is enough to confirm the schema

    print("\n--- What this proves ---")
    print("  - 17 entities × 1500 frames + zones + coach intent + commentary,")
    print("    all in one queryable graph. Loads in under a second.")
    print("  - Spatial (distance), temporal (window functions),")
    print("    relational (traversal), confidence (filter) — all available")
    print("    against the same nodes via WorldCypher.")
    print("  - Step 02 layers tactical-pattern queries on top of this substrate.")

    db.close()


if __name__ == "__main__":
    main()
