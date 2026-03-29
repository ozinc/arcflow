# Use Case: Sports Analytics

Track players in real time, compute formations, detect events, and analyze match patterns.

## The problem

Sports analytics requires:
- **Spatial tracking** — player positions at 50Hz (22 players, 90 minutes = 5.94M data points)
- **Temporal queries** — "Where was player X at minute 35?"
- **Graph relationships** — team membership, passing networks, marking assignments
- **Real-time algorithms** — nearest player to ball, formation detection, offside detection

## Why ArcFlow

One engine handles the spatial data, temporal queries, graph algorithms, and real-time computation. No separate databases for positions, events, and relationships.

## Implementation

```typescript
import { open } from '@arcflow/sdk'

const db = open('./match-data')

// Create players with positions
db.batchMutate([
  "CREATE (p:Player {id: 'p1', name: 'Alice', team: 'home', number: 10, x: 52.3, y: 34.1, speed: 7.2})",
  "CREATE (p:Player {id: 'p2', name: 'Bob', team: 'home', number: 7, x: 65.0, y: 20.5, speed: 4.1})",
  "CREATE (ball:Ball {x: 50.0, y: 33.5, speed: 12.4})",
])

// Query: fast players
const fast = db.query("MATCH (p:Player) WHERE p.speed > 5.0 RETURN p.name, p.speed ORDER BY p.speed DESC")

// Query: team formations
const home = db.query("MATCH (p:Player) WHERE p.team = 'home' RETURN p.name, p.x, p.y ORDER BY p.x")

// Algorithms: passing network centrality
const centrality = db.query("CALL algo.pageRank()")

// Algorithms: player clusters (formations)
const formations = db.query("CALL algo.louvain()")
```

## See also

- [examples/sports-tracking/](../../examples/sports-tracking/) — runnable example
