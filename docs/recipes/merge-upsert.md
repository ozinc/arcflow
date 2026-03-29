# Recipe: MERGE (Upsert)

MERGE is the upsert pattern — find a matching node, or create it if it doesn't exist.

## Basic MERGE

```typescript
// First call creates the node
db.mutate("MERGE (n:Person {id: 'p1', name: 'Alice'})")

// Second call finds the existing node — no duplicate
db.mutate("MERGE (n:Person {id: 'p1', name: 'Alice'})")
```

## MERGE with ON CREATE / ON MATCH

```typescript
db.mutate("MERGE (n:Person {id: $id}) ON CREATE SET n.name = $name ON MATCH SET n.lastSeen = $ts", {
  id: 'p1', name: 'Alice', ts: Date.now()
})
```

## MERGE for idempotent pipelines

MERGE is ideal for data pipelines that may re-run:

```typescript
const entities = [
  "MERGE (p:Person {id: 'p1', name: 'Alice', workspaceId: 'ws1'})",
  "MERGE (p:Person {id: 'p2', name: 'Bob', workspaceId: 'ws1'})",
  "MERGE (o:Org {id: 'o1', name: 'Acme', workspaceId: 'ws1'})",
]
// Safe to re-run — existing nodes are matched, not duplicated
db.batchMutate(entities)
```

## MERGE relationships

```typescript
// Create relationship only if it doesn't exist
db.mutate("MATCH (a:Person {id: 'p1'}) MATCH (b:Org {id: 'o1'}) MERGE (a)-[:WORKS_AT]->(b)")
```

**Note:** MERGE on relationships matches by type and endpoints. Properties on the MERGE pattern are used for matching, not just creation.
