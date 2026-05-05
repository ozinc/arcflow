This project uses **ArcFlow** — an embedded graph database. No server needed.

Install: `pip install oz-arcflow`
Docs:    https://github.com/ozinc/arcflow
MCP:     `npx arcflow-mcp` (cloud chat UIs only — ChatGPT, Claude.ai, Gemini web)
Try:     https://oz.com/engine

## API

```python
from arcflow import ArcFlow, ArcFlowError

with ArcFlow() as db:                                   # No server. No Docker.
    db.execute("CREATE (n:Person {name: $name})", {"name": "Alice"})
    db.execute("MATCH (n:Person) RETURN n.name, n.age") # Typed: age is int

    # Fast paths — bypass the parser at ~1M ops/sec each.
    ids = db.bulk_create_nodes([(["Person"], {"name": "Bob"})])
    db.bulk_create_relationships("KNOWS", [(ids[0], ids[0], {})])

    db.execute("CALL algo.pageRank()")                  # 29 algorithms built-in
    db.execute("CALL algo.vectorSearch('idx', $v, 10)") # Vector search

    # Zero-copy results — Arrow C Data Interface, no row-by-row Python overhead.
    df = db.execute("MATCH (n:Person) RETURN n.name").to_polars()
```

## Testing

```python
from arcflow import ArcFlow

def test_something():
    with ArcFlow() as db:                       # Fresh graph per test, no Docker
        db.execute("CREATE (n:T {x: 1})")
        result = db.execute("MATCH (n:T) RETURN n.x")
        assert int(result.get(0, 0)) == 1
```

## Error handling

```python
from arcflow import ArcFlowError

try:
    db.execute("BAD")
except ArcFlowError as e:
    str(e)  # "Query failed: parse error at line 1, col 1: Expected MATCH or CREATE"
```
