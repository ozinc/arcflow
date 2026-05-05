This project uses **ArcFlow** — an embedded graph database. No server needed.

## Commands

```bash
pip install -e .[dev]                # Install with dev tools
python -m {{PACKAGE_NAME}}.main      # Run the example
pytest                               # Run tests
```

## Database

```python
from arcflow import ArcFlow

with ArcFlow() as db:                                   # In-memory (dev/test)
    pass
with ArcFlow("./data") as db:                           # Persistent (production)
    pass

db.execute("CREATE (n:Person {name: 'Alice'})")         # Write
db.execute("MATCH (n:Person) RETURN n.name")            # Read (typed results)
db.execute("MATCH (n {id: $id}) RETURN n", {"id": 42})  # Parameters

# Fast paths — bypass the Cypher parser, ~1M ops/sec each.
db.bulk_create_nodes([(["Person"], {"name": "Alice"})])
db.bulk_create_relationships("KNOWS", [(start_id, end_id, {})])

# Zero-copy results — Arrow C Data Interface under the hood.
result = db.execute("MATCH (n:Person) RETURN n.name, n.age")
result.to_arrow()    # pyarrow.RecordBatch
result.to_polars()   # polars.DataFrame
result.to_pandas()   # pandas.DataFrame
```

## WorldCypher

```cypher
CREATE (n:Label {key: 'value'})
MATCH (n:Label) WHERE n.key = $value RETURN n
MATCH (a)-[:REL]->(b) RETURN a.name, b.name
MERGE (n:Label {id: 'unique'})
CALL algo.pageRank()
CALL algo.vectorSearch('index', $vector, 10)
```

## Docs

- Full docs: https://github.com/ozinc/arcflow
- AGENTS.md (full Python API reference): https://github.com/ozinc/arcflow-docs/blob/main/AGENTS.md
- MCP server: `npx arcflow-mcp` (cloud chat UIs only — ChatGPT, Claude.ai, Gemini web)
- Try in browser: https://oz.com/engine
