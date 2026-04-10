This project uses **ArcFlow** — an embedded graph database. No server needed.

## Commands

```bash
npm start          # Run src/index.ts
npm test           # Run tests (Vitest)
npm run dev        # Watch mode
```

## Database

```typescript
import { openInMemory, open } from 'arcflow'

const db = openInMemory()                         // In-memory (dev/test)
const db = open('./data')                          // Persistent (production)

db.mutate("CREATE (n:Person {name: 'Alice'})")     // Write
db.query("MATCH (n:Person) RETURN n.name")         // Read (typed results)
db.query("MATCH (n {id: $id}) RETURN n", { id })   // Parameters
db.batchMutate([...queries])                       // Bulk writes
db.query("CALL algo.pageRank()")                   // Algorithms — no setup
db.stats()                                         // { nodes, relationships, indexes }
db.close()
```

## WorldCypher

```cypher
CREATE (n:Label {key: 'value'})
MATCH (n:Label) WHERE n.key = 'value' RETURN n
MATCH (a)-[:REL]->(b) RETURN a.name, b.name
MERGE (n:Label {id: 'unique'})
CALL algo.pageRank()
CALL algo.vectorSearch('index', $vector, 10)
CALL db.stats()
```

## Docs

- Full docs: https://github.com/ozinc/arcflow
- MCP server: `npx arcflow-mcp` (cloud chat UIs only — ChatGPT, Claude.ai, Gemini web)
- Try in browser: https://arcflow.dev/engine
