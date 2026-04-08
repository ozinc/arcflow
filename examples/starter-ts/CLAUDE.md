# CLAUDE.md

This project uses **ArcFlow** as its graph database.

## Key Commands

```bash
npm start          # Run the project
npm test           # Run tests
npm run dev        # Watch mode
```

## Database

- ArcFlow is an embedded graph database — no server needed
- Use `openInMemory()` for development and testing
- Use `open('./data')` for persistent storage
- Query language: WorldCypher (ArcFlow's GQL dialect — ISO/IEC 39075 + spatial/temporal/reactive extensions)

## API

```typescript
import { openInMemory, open } from 'arcflow'

const db = openInMemory()              // In-memory (tests, prototyping)
const db = open('./data')              // Persistent (production)

db.query('MATCH (n) RETURN n')         // Read queries
db.mutate('CREATE (n:Label {k: v})')   // Write queries
db.batchMutate([...queries])           // Bulk writes
db.stats()                             // { nodes, relationships, indexes }
db.close()                             // Flush and close
```

## GQL / WorldCypher Quick Reference

```cypher
// Create nodes and relationships
CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})

// Query with pattern matching
MATCH (p:Person)-[:KNOWS]->(friend)
WHERE p.name = 'Alice'
RETURN friend.name

// Spatial queries
MATCH (p:Player) WHERE WITHIN(p.pos, Zone('penalty_box'))

// Graph algorithms
CALL algo.pageRank() YIELD node, score
RETURN node.name, score ORDER BY score DESC

// Vector search
CALL vector.search('embeddings', [0.1, 0.2, ...], 10) YIELD node, distance
```

## Docs

- Full docs: https://oz.com/docs
- GQL / WorldCypher reference: https://oz.com/docs/worldcypher
- Coding agents (Claude Code, Codex): use `arcflow query '...'` CLI binary — exits in <10ms
- Cloud chat UIs (ChatGPT, Claude.ai): `npx arcflow-mcp`
