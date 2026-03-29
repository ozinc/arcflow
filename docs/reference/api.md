# API Reference

Complete TypeScript SDK API.

## Module exports

```typescript
import { open, openInMemory, ArcflowError } from '@arcflow/sdk'
```

## `open(dataDir: string): ArcflowDB`

Open a persistent graph database. Data is WAL-journaled to disk.

```typescript
const db = open('./data/graph')
```

## `openInMemory(): ArcflowDB`

Open an in-memory graph database. Data is lost when the process exits. Ideal for testing.

```typescript
const db = openInMemory()
```

## `ArcflowDB`

The main database interface.

### `db.version(): string`

Returns the engine version string.

### `db.query(cypher: string, params?: QueryParams): QueryResult`

Execute a read query. Returns typed results.

```typescript
const result = db.query("MATCH (n:Person) RETURN n.name, n.age")
const result = db.query("MATCH (n {id: $id}) RETURN n", { id: 'p1' })
```

### `db.mutate(cypher: string, params?: QueryParams): MutationResult`

Execute a mutating query (CREATE, MERGE, SET, DELETE).

```typescript
db.mutate("CREATE (n:Person {name: $name})", { name: 'Alice' })
```

### `db.batchMutate(queries: string[]): number`

Execute multiple mutations under a single write lock. Returns count of mutations applied.

```typescript
const count = db.batchMutate([
  "MERGE (a:Person {id: 'p1', name: 'Alice'})",
  "MERGE (b:Person {id: 'p2', name: 'Bob'})",
])
```

### `db.isHealthy(): boolean`

Returns `true` if the database is operational. Returns `false` after `close()`.

### `db.stats(): GraphStats`

Returns node, relationship, and index counts.

```typescript
const s = db.stats()
console.log(s.nodes, s.relationships, s.indexes)
```

### `db.close(): void`

Close the database and flush WAL. All subsequent operations throw `ArcflowError`.

## `QueryParams`

```typescript
type QueryParams = Record<string, string | number | boolean | null>
```

## `QueryResult`

```typescript
interface QueryResult {
  columns: string[]       // Column names
  rows: TypedRow[]        // Typed row accessors
  rowCount: number        // Number of rows
  computeMs: number       // Execution time (ms)
}
```

## `MutationResult`

Extends `QueryResult` with mutation statistics.

```typescript
interface MutationResult extends QueryResult {
  nodesCreated: number
  nodesDeleted: number
  relationshipsCreated: number
  relationshipsDeleted: number
  propertiesSet: number
}
```

## `TypedRow`

### `row.get(column: string): string | number | boolean | null`

Get a typed value by column name. Supports both full (`n.name`) and short (`name`) column names.

### `row.toObject(): Record<string, string | number | boolean | null>`

Get all columns as a typed key-value object.

## `GraphStats`

```typescript
interface GraphStats {
  nodes: number
  relationships: number
  indexes: number
}
```

## `ArcflowError`

```typescript
class ArcflowError extends Error {
  code: string                // "EXPECTED_KEYWORD", "LOCK_POISONED", etc.
  category: ErrorCategory     // "parse" | "validation" | "execution" | "integration"
  suggestion?: string         // Recovery hint (when available)
}
```

### `ArcflowError.fromNapiError(err: unknown): ArcflowError`

Parse a raw napi error into a structured ArcflowError. Used internally by the SDK.
