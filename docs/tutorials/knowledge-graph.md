# Tutorial: Build a Knowledge Graph

Build a knowledge graph that models people, organizations, and the facts connecting them — the core pattern behind applications like CRM, intelligence analysis, and entity resolution.

## What you'll build

A graph that tracks:
- **People** with names, roles, and metadata
- **Organizations** with industries and locations
- **Facts** — typed, confidence-scored relationships between entities

## 1. Setup

```typescript
import { open } from '@arcflow/sdk'

const db = open('./knowledge-graph')
```

## 2. Create entities

```typescript
// People
db.mutate("CREATE (p:Person {id: 'p1', name: 'Alice Chen', role: 'CTO', city: 'San Francisco'})")
db.mutate("CREATE (p:Person {id: 'p2', name: 'Bob Smith', role: 'VP Engineering', city: 'New York'})")
db.mutate("CREATE (p:Person {id: 'p3', name: 'Carol Davis', role: 'Data Scientist', city: 'London'})")

// Organizations
db.mutate("CREATE (o:Org {id: 'o1', name: 'Acme Corp', industry: 'tech', hq: 'San Francisco'})")
db.mutate("CREATE (o:Org {id: 'o2', name: 'Globex Inc', industry: 'finance', hq: 'New York'})")
```

## 3. Create relationships

```typescript
// Employment relationships
db.mutate("MATCH (p:Person {id: 'p1'}) MATCH (o:Org {id: 'o1'}) MERGE (p)-[:WORKS_AT {since: 2019}]->(o)")
db.mutate("MATCH (p:Person {id: 'p2'}) MATCH (o:Org {id: 'o2'}) MERGE (p)-[:WORKS_AT {since: 2021}]->(o)")

// Social connections
db.mutate("MATCH (a:Person {id: 'p1'}) MATCH (b:Person {id: 'p2'}) MERGE (a)-[:KNOWS {context: 'conference'}]->(b)")
```

## 4. Add facts with confidence scores

Facts are first-class entities — not just edges. This lets you track provenance and confidence:

```typescript
// Create a fact node
db.mutate("CREATE (f:Fact {uuid: 'f1', predicate: 'advises', confidence: 0.87, source: 'press-release'})")

// Link fact to subject and object
db.mutate("MATCH (p:Person {id: 'p1'}) MATCH (f:Fact {uuid: 'f1'}) MERGE (p)-[:SUBJECT_OF]->(f)")
db.mutate("MATCH (f:Fact {uuid: 'f1'}) MATCH (o:Org {id: 'o2'}) MERGE (f)-[:OBJECT_IS]->(o)")
```

## 5. Query the knowledge graph

### Find all connections for a person

```typescript
const connections = db.query(
  "MATCH (p:Person {id: $id})-[r]->(target) RETURN labels(target), target.name",
  { id: 'p1' }
)
for (const row of connections.rows) {
  console.log(row.toObject())
}
```

### Find high-confidence facts

```typescript
const facts = db.query(
  "MATCH (s)-[:SUBJECT_OF]->(f:Fact)-[:OBJECT_IS]->(o) WHERE f.confidence > $threshold RETURN s.name, f.predicate, o.name, f.confidence ORDER BY f.confidence DESC",
  { threshold: 0.8 }
)
```

### Cross-entity queries (multi-MATCH)

```typescript
// Find people at the same organization
const colleagues = db.query(`
  MATCH (a:Person)-[:WORKS_AT]->(o:Org)
  MATCH (b:Person)-[:WORKS_AT]->(o)
  WHERE a.id <> b.id
  RETURN a.name, b.name, o.name
`)
```

## 6. Run graph algorithms

```typescript
// Who's most central in the network?
const pr = db.query("CALL algo.pageRank()")
for (const row of pr.rows) {
  console.log(`${row.get('name')}: ${row.get('rank')}`)
}

// Find communities
const communities = db.query("CALL algo.louvain()")
```

## 7. Batch ingestion

For pipeline-style data loading, use `batchMutate`:

```typescript
const entities = [
  "MERGE (p:Person {id: 'p4', name: 'Diana Lee', role: 'CEO'})",
  "MERGE (o:Org {id: 'o3', name: 'NovaTech', industry: 'biotech'})",
  "MERGE (f:Fact {uuid: 'f2', predicate: 'founded', confidence: 0.95})",
]
db.batchMutate(entities)
```

## Next steps

- [Entity Linking Tutorial](entity-linking.md) — deep dive into multi-MATCH patterns
- [Vector Search Tutorial](vector-search.md) — add semantic search to your knowledge graph
- [Batch Projection Recipe](../recipes/batch-projection.md) — high-throughput data loading
