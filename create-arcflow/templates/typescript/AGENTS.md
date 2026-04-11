This project uses **ArcFlow** — an embedded graph database. No server needed.

Install: `npm install arcflow`
Docs: https://github.com/ozinc/arcflow
MCP: `npx arcflow-mcp` (cloud chat UIs only — ChatGPT, Claude.ai, Gemini web)
Try: https://oz.com/engine

## API

```typescript
import { openInMemory, open, ArcflowError } from 'arcflow'

const db = openInMemory()                          // No server. No Docker.
db.mutate("CREATE (n:Person {name: $name})", { name: 'Alice' })
db.query("MATCH (n:Person) RETURN n.name, n.age")  // Typed: age is number
db.batchMutate(["MERGE (a:X {id: '1'})", "MERGE (b:X {id: '2'})"])
db.query("CALL algo.pageRank()")                   // 30+ algorithms
db.query("CALL algo.vectorSearch('idx', $v, 10)")  // Vector search
db.stats()                                         // { nodes, relationships, indexes }
db.close()
```

## Testing

```typescript
const db = openInMemory()  // Fresh graph per test, no cleanup, no Docker
db.mutate("CREATE (n:Test {x: 1})")
expect(db.query("MATCH (n:Test) RETURN n.x").rows[0].get('x')).toBe(1)
```

## Error handling

```typescript
try { db.query("BAD") } catch (e) {
  if (e instanceof ArcflowError) {
    e.code        // "EXPECTED_KEYWORD"
    e.category    // "parse" | "validation" | "execution" | "integration"
    e.suggestion  // "Expected MATCH or CREATE"
  }
}
```
