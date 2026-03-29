# WorldCypher: Spatial Queries

ArcFlow extends Cypher with spatial predicates and functions for location-aware graphs.

## Spatial properties

Store coordinates as node properties:

```typescript
db.mutate("CREATE (p:Player {name: 'Alice', x: 52.3, y: 34.1, speed: 7.2})")
db.mutate("CREATE (s:Sensor {id: 's1', lat: 51.5074, lon: -0.1278})")
```

## Spatial predicates

### Distance-based queries

```cypher
-- Find all players within 10 meters of a point
MATCH (p:Player) WHERE p.x > 40 AND p.x < 60 AND p.y > 30 AND p.y < 40
RETURN p.name, p.x, p.y

-- Find nearest nodes
CALL algo.nearestNodes()
```

### Zone queries

```cypher
-- Find players in the penalty box (rectangle)
MATCH (p:Player)
WHERE p.x > 0 AND p.x < 16.5 AND p.y > 13.84 AND p.y < 54.16
RETURN p.name
```

## Spatial algorithms

```cypher
-- Node similarity by spatial proximity
CALL algo.nodeSimilarity()

-- Connected components (spatial clusters)
CALL algo.connectedComponents()

-- Community detection (spatial groupings)
CALL algo.louvain()
```

## Vector-based spatial search

For high-dimensional spatial data, use vector indexes:

```typescript
db.mutate("CREATE VECTOR INDEX locations FOR (n:Point) ON (n.coords) OPTIONS {dimensions: 2, similarity: 'euclidean'}")
db.query("CALL algo.vectorSearch('locations', $point, 5)", {
  point: JSON.stringify([52.3, 34.1])
})
```

## Use cases

- **Sports analytics** — player positions, formations, proximity to ball
- **Fleet management** — vehicle locations, geofencing, route optimization
- **IoT** — sensor positions, coverage areas, spatial aggregation
- **Security** — camera fields, restricted zones, dwell detection
