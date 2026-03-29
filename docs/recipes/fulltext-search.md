# Recipe: Full-Text Search

BM25-scored full-text search over node properties.

## Create a full-text index

```typescript
db.mutate("CREATE FULLTEXT INDEX person_search FOR (n:Person) ON (n.name)")
```

## Search

```typescript
const results = db.query("CALL db.index.fulltext.queryNodes('person_search', 'Alice')")
for (const row of results.rows) {
  console.log(row.get('name'), row.get('score'))
}
```

## Search with a variable query

```typescript
const results = db.query(
  "CALL db.index.fulltext.queryNodes('person_search', $query)",
  { query: userSearchTerm }
)
```

## Multi-property index

```typescript
db.mutate("CREATE FULLTEXT INDEX doc_search FOR (n:Document) ON (n.title, n.body)")
```

## List existing indexes

```typescript
const indexes = db.query("CALL db.fulltextIndexes")
```
