# Step 01 — Schema Design

Goal: choose how player tracking data lives in ArcFlow before writing any code.

## The data shape

Each Parquet row:

```
game_id, play_id, frame_id, timestamp, player_id, team, x, y, speed
```

For 1100 rows that is ~50 KB. For one full NFL game (~150 plays × 100 frames ×
22 players ≈ 330 K rows), it is ~15 MB. For a season, scale linearly.

## Two schema options

### Option A — One node per (player, frame)

```
(:Tracking {game_id, play_id, frame_id, player_id, x, y, speed})
```

Simple. One row of Parquet maps to one node. Reads are easy:

```cypher
MATCH (t:Tracking {player_id: 'P01', play_id: 1})
RETURN t.frame_id, t.x, t.y
ORDER BY t.frame_id
```

**Cost:** N×F nodes (N players, F frames). 330 K nodes per game. Scales, but
trajectories of one player require a sort.

### Option B — One node per Player + Frame node per timestamp + edge per observation

```
(:Player {player_id, team})-[:OBSERVED_AT {x, y, speed}]->(:Frame {game_id, play_id, frame_id, timestamp})
```

Player identity is stable. Frame identity is shared across players at the
same timestamp.

**Cost:** N + F nodes + N×F edges. More relationships, but:

- Per-player trajectory is one MATCH along OBSERVED_AT, ordered by Frame.
- Per-frame snapshot ("everyone at frame 42") is one MATCH on Frame.
- Cross-player queries ("nearest opponent to player X at frame 42") become
  a graph traversal, not a self-join.

This is the **graph-native** schema. We pick it.

## The chosen schema

```cypher
// Player nodes — one per player_id, identity stable across plays
(:Player {player_id, team})

// Frame nodes — one per (game_id, play_id, frame_id) tuple
(:Frame {game_id, play_id, frame_id, timestamp})

// Edge — one per Parquet row
(:Player)-[:OBSERVED_AT {x, y, speed}]->(:Frame)
```

For 1100 rows: 22 Player nodes + 50 Frame nodes (5 plays × 10 frames) + 1100
OBSERVED_AT edges. The graph is dense enough that path queries (nearest
opponent, closest receiver) become trivial.

## Why this maps to ArcFlow's strengths

- **Spatial:** position lives on the *edge*, not the node. ArcFlow's spatial
  index can be applied to OBSERVED_AT edges keyed by (Frame, Player) →
  (x, y) — see step 03.
- **Temporal:** Frame nodes carry the timestamp. WorldCypher's temporal
  predicates (BETWEEN, AS OF, ORDER BY t.timestamp) operate on Frame.
- **Confidence:** sensor-tracked positions are imperfect. In production,
  add `_confidence` to OBSERVED_AT edges (camera detection score, GPS
  accuracy, etc.). Filter in queries with `WHERE r._confidence > 0.7`.

## What we are NOT doing

- Storing every (player, frame) as one big rectangular property bag on a
  shared "Game" node. That collapses graph structure to a hash table.
- Modelling teams as a fixed pair (`team: 'home'`/`'away'` is a property,
  not an edge). For a single game, team membership is stable; for
  season-level analysis, add `(:Team)<-[:MEMBER_OF]-(:Player)`.

## Next

[`02-parquet-load.py`](./02-parquet-load.py) reads `data/sample.parquet`,
batches the rows, and emits the three node/edge types into ArcFlow.
