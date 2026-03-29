# Sample Fixtures

Ready-to-load sample datasets for examples and testing.

## Usage

```typescript
import { readFileSync } from 'fs'
import { openInMemory } from '@arcflow/sdk'

const db = openInMemory()
const fixture = readFileSync('./fixtures/social-network.cypher', 'utf-8')
const lines = fixture.split('\n').filter(l => l.trim() && !l.startsWith('//'))
db.batchMutate(lines)
```

## Available fixtures

| File | Description | Nodes | Relationships |
|---|---|---|---|
| `social-network.cypher` | 6 people, 2 orgs, KNOWS/WORKS_AT/MENTORS | 8 | 13 |
| `knowledge-graph.cypher` | Entities + confidence-scored facts (BASAL pattern) | 12 | 13 |
