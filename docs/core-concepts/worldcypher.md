# WorldCypher Query Language

WorldCypher is ArcFlow's query language. It's compatible with Cypher (Neo4j) and extends it with temporal queries, reactive programming, vector search, and graph algorithms.

If you know Cypher, you know WorldCypher. If you don't, it reads like ASCII art.

## Reading data

### MATCH — find patterns

```cypher
-- Find all people
MATCH (n:Person) RETURN n.name, n.age

-- Find by property
MATCH (n:Person {name: 'Alice'}) RETURN n

-- Find with conditions
MATCH (n:Person) WHERE n.age > 25 RETURN n.name ORDER BY n.age DESC LIMIT 10
```

### Relationship traversal

```cypher
-- One hop
MATCH (a:Person)-[:KNOWS]->(b:Person) RETURN a.name, b.name

-- Variable-length (1 to 3 hops)
MATCH (a:Person {name: 'Alice'})-[:KNOWS*1..3]->(b) RETURN b.name

-- Any relationship type
MATCH (a:Person)-[r]->(b) RETURN a.name, type(r), b.name
```

### Multi-MATCH (cross-entity joins)

```cypher
-- Find a person and a company independently, return both
MATCH (p:Person {id: 'p1'}) MATCH (c:Company {id: 'c1'}) RETURN p.name, c.name
```

### Aggregations

```cypher
MATCH (n:Person) RETURN count(*) AS total, avg(n.age) AS avgAge
MATCH (n:Person) RETURN n.city, count(*) AS residents ORDER BY residents DESC
```

## Writing data

### CREATE — add new data

```cypher
CREATE (n:Person {name: 'Alice', age: 30})
CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})
```

### MERGE — find or create

```cypher
-- Creates only if no matching node exists
MERGE (n:Person {id: 'p1', name: 'Alice'})
```

### SET — update properties

```cypher
MATCH (n:Person {name: 'Alice'}) SET n.age = 31
```

### DELETE — remove data

```cypher
MATCH (n:Person {name: 'Alice'}) DELETE n
MATCH (n:Person {name: 'Alice'}) DETACH DELETE n  -- also removes relationships
```

### REMOVE — delete a property

```cypher
MATCH (n:Person {name: 'Alice'}) REMOVE n.email
```

## Parameters

Always use parameters for user-supplied values — they prevent injection and improve readability:

```typescript
// Good — parameterized
db.query("MATCH (n:Person {name: $name}) RETURN n", { name: userInput })

// Bad — string interpolation (injection risk)
db.query(`MATCH (n:Person {name: '${userInput}'}) RETURN n`)
```

## String functions

```cypher
WHERE n.name CONTAINS 'ali'
WHERE n.name STARTS WITH 'A'
RETURN toLower(n.name) AS lowerName
RETURN COALESCE(n.email, 'none') AS email
```

## Algorithms

Run graph algorithms directly — no projection setup:

```cypher
CALL algo.pageRank()
CALL algo.louvain()
CALL algo.betweenness()
CALL algo.vectorSearch('my_index', $vector, 10)
```

## Temporal queries

Query the graph at a point in time:

```cypher
MATCH (n:Person) AS OF 1700000000 RETURN n.name
```

## Full-text search

```cypher
CREATE FULLTEXT INDEX person_search FOR (n:Person) ON (n.name)
CALL db.index.fulltext.queryNodes('person_search', 'Alice')
```

## Reactive queries

```cypher
-- Standing query — continuously re-evaluates
LIVE MATCH (n:Person) WHERE n.score > 0.9 RETURN n

-- Live algorithm — incrementally maintained
LIVE CALL algo.pageRank()

-- Persistent view
CREATE LIVE VIEW top_people AS MATCH (n:Person) WHERE n.score > 0.9 RETURN n.name
```

See the [Compatibility Matrix](../reference/compatibility.md) for the complete feature table.
