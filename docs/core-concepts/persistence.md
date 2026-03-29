# Persistence & WAL

ArcFlow uses a write-ahead log (WAL) for durability. All mutations are journaled before they're applied.

## In-memory vs. persistent

```typescript
import { open, openInMemory } from '@arcflow/sdk'

// In-memory: fast, lost on exit. Great for tests.
const mem = openInMemory()

// Persistent: WAL-journaled, survives crashes and restarts.
const disk = open('./data/graph')
```

## How persistence works

1. **Write**: mutations are appended to the WAL before being applied
2. **Crash**: if the process dies, the WAL retains all committed mutations
3. **Recovery**: on next `open()`, the WAL replays automatically — no data loss
4. **Checkpoint**: periodically compacts the WAL into a snapshot

```typescript
const db = open('./my-graph')

// This mutation is WAL-journaled
db.mutate("CREATE (n:Important {data: 'critical'})")

// Process crashes here...

// On restart — WAL replays, data is recovered
const db2 = open('./my-graph')
const result = db2.query("MATCH (n:Important) RETURN n.data")
console.log(result.rows[0].get('data'))  // "critical"
```

## Checkpoints

Compact the WAL into a snapshot to reduce recovery time:

```typescript
db.mutate("CALL db.checkpoint()")
```

## Integrity verification

Compute a cryptographic fingerprint of the graph state:

```typescript
const fp = db.query("CALL db.fingerprint")
console.log(fp.rows[0].get('fingerprint'))  // sha256:...
```

## Data directory structure

```
./my-graph/
├── worldcypher.snapshot.json   # Compacted snapshot (after checkpoint)
└── wal/                        # Write-ahead log segments
```

## Closing the database

Call `close()` for a clean shutdown that flushes the WAL:

```typescript
db.close()
```

After closing, all operations will throw an `ArcflowError` with code `DB_CLOSED`.
