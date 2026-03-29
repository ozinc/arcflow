# Parameterized Queries

Use `$param` placeholders to pass values safely into queries.

## Why parameters?

1. **Security** — prevents query injection (values are substituted before compilation)
2. **Readability** — separates query shape from data
3. **Performance** — query plans can be cached independently of values

## Basic usage

```typescript
const result = db.query(
  "MATCH (n:Person {name: $name}) RETURN n.age",
  { name: 'Alice' }
)
```

## Supported value types

The SDK accepts typed parameters and coerces them to the engine format:

```typescript
db.query("MATCH (n {id: $id, score: $score, active: $active}) RETURN n", {
  id: 'entity-1',     // string
  score: 42,           // number → "42"
  active: true,        // boolean → "true"
})
```

| TypeScript Type | Coerced To | Example |
|---|---|---|
| `string` | string | `'Alice'` → `'Alice'` |
| `number` | string representation | `42` → `'42'` |
| `boolean` | `'true'` / `'false'` | `true` → `'true'` |
| `null` | `'null'` | `null` → `'null'` |

## Multiple parameters

```typescript
db.query(
  "MATCH (a:Person {id: $pid}) MATCH (b:Org {id: $oid}) RETURN a.name AS personName, b.name AS orgName",
  { pid: 'p1', oid: 'o1' }
)
```

## Parameters in mutations

```typescript
db.mutate(
  "CREATE (n:Person {name: $name, age: $age})",
  { name: 'Alice', age: 30 }
)

db.mutate(
  "MATCH (n:Person {name: $name}) SET n.age = $age",
  { name: 'Alice', age: 31 }
)
```

## Arrays / vectors

For array-type values (like embeddings), pass as JSON string:

```typescript
db.query(
  "CALL algo.vectorSearch('my_index', $vector, 10)",
  { vector: JSON.stringify([0.1, 0.2, 0.3, 0.4]) }
)
```
