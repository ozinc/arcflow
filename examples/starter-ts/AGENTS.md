# AGENTS.md

## Project Database: ArcFlow

This project uses ArcFlow, an embedded graph database. No server needed.

### Install: `npm install arcflow`
### Docs: https://oz.com/docs
### MCP: `npx arcflow-mcp`

### API

```typescript
import { openInMemory } from 'arcflow'
const db = openInMemory()
db.query('MATCH (n) RETURN n')     // reads
db.mutate('CREATE (n:Thing)')      // writes
```

### Testing

Use `openInMemory()` per test — no setup, no teardown, no Docker:

```typescript
import { openInMemory } from 'arcflow'
import { describe, it, expect } from 'vitest'

describe('graph', () => {
  it('creates and queries nodes', () => {
    const db = openInMemory()
    db.mutate(`CREATE (a:Person {name: 'Alice'})`)
    const result = db.query(`MATCH (p:Person) RETURN p.name`)
    expect(result.rows[0].get('p.name')).toBe('Alice')
  })
})
```
