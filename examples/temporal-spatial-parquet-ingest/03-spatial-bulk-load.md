# Step 03 — Spatial Bulk-Load

Goal: explain why position lives on the OBSERVED_AT edge, not the Player node,
and how to query nearest-entity queries efficiently.

## The shape

Position is per-frame. A Player node has identity but no fixed (x, y) — they
move. So position belongs on the **observation** (the edge), not the
**identity** (the node).

```cypher
(:Player)-[:OBSERVED_AT {x, y, speed}]->(:Frame)
```

## Querying "everyone at frame 42"

Per-frame snapshot:

```cypher
MATCH (p:Player)-[r:OBSERVED_AT]->(f:Frame)
WHERE f.play_id = 1 AND f.frame_id = 4
RETURN p.player_id, r.x, r.y, r.speed
ORDER BY r.x
```

This returns 22 rows for our sample. Sub-millisecond on the loaded graph
because Frame nodes have the unique key constraint on (game_id, play_id,
frame_id) — see step 01.

## Querying "nearest opponent to player X at frame 42"

```cypher
MATCH (p:Player {player_id: 'P01'})-[r1:OBSERVED_AT]->(f:Frame {play_id: 1, frame_id: 4}),
      (q:Player)-[r2:OBSERVED_AT]->(f)
WHERE q.team <> p.team
WITH q, point({x: r1.x, y: r1.y}) AS p_pos,
        point({x: r2.x, y: r2.y}) AS q_pos
RETURN q.player_id, distance(p_pos, q_pos) AS dist
ORDER BY dist
LIMIT 1
```

For our sample (22 players, 11 opponents), this is a linear scan — fast.

## Scaling to many entities per frame

When a frame has 1000+ entities (smart-city sensors, drone fleet, dense
crowd), the per-frame scan stops being free. Two ArcFlow tools apply:

1. **R*-tree spatial index** — register the (x, y) of every OBSERVED_AT
   edge into the live spatial index. KNN, radius, frustum queries all
   become sub-millisecond regardless of frame size.

2. **Property index on (play_id, frame_id)** — already implicit in the
   schema; ensures the per-frame WHERE filter is O(1).

For our 1100-row recipe, neither is required. We document the tools so the
next step up the scale curve is obvious.

## What we are NOT doing

- Mirroring (x, y) onto the Player node. That makes "where is everyone right
  now" trivial — but only for a single live frame. Trajectories require
  per-frame storage anyway, and duplicating creates a consistency hazard.
- Sharding across plays. For one game, the graph is small. For a season,
  partition by `game_id`.

## Next

[`04-temporal-queries.py`](./04-temporal-queries.py) — per-player trajectory,
LAG-style frame-to-frame deltas, total distance traveled.
