# arcflow-mcp

MCP server for ArcFlow. Lets AI agents query your graph database directly — no code generation needed.

## Quick start

```bash
npx arcflow-mcp
```

Or with persistent data:

```bash
npx arcflow-mcp --data-dir ./my-graph
```

## Add to Claude Code

```json
// ~/.claude/settings.json
{
  "mcpServers": {
    "arcflow": {
      "command": "npx",
      "args": ["arcflow-mcp", "--data-dir", "./data/graph"]
    }
  }
}
```

Or per-project in `.claude/settings.json`:

```json
{
  "mcpServers": {
    "arcflow": {
      "command": "npx",
      "args": ["arcflow-mcp"]
    }
  }
}
```

## Add to Cursor

```json
// .cursor/mcp.json
{
  "mcpServers": {
    "arcflow": {
      "command": "npx",
      "args": ["arcflow-mcp"]
    }
  }
}
```

## Tools

| Tool | Description | Read/Write |
|---|---|---|
| `get_schema` | Labels, relationship types, properties, indexes, stats | Read |
| `get_capabilities` | Algorithms, procedures, window functions, query features | Read |
| `read_query` | Execute read-only WorldCypher (MATCH, CALL algo.*, CALL db.*) | Read |
| `write_query` | Execute mutations (CREATE, SET, DELETE, MERGE) | Write |
| `graph_rag` | Trusted GraphRAG pipeline — answer questions from the knowledge graph | Read |

## How it works

The MCP server runs ArcFlow **in-process** via the native napi-rs binding. No separate database server needed. The agent talks to the graph engine directly through stdio JSON-RPC.

```
Agent ←→ stdio JSON-RPC ←→ arcflow-mcp ←→ ArcFlow engine (in-process)
```

## Why this matters

Without MCP, agents generate code to query databases. With MCP, agents **use** the database directly:

| Without MCP | With MCP |
|---|---|
| "Write me code that queries Neo4j for..." | "Query my graph: who's connected to Alice?" |
| Agent generates driver code, connection, query | Agent calls `read_query` tool directly |
| User runs the code manually | Agent gets results immediately |

## Examples

Agent asks: "What's in my graph?"
→ Calls `get_schema` → sees labels, properties, stats

Agent asks: "Who are the most important people?"
→ Calls `read_query` with `CALL algo.pageRank()`

Agent asks: "Add Alice to the graph"
→ Calls `write_query` with `CREATE (n:Person {name: 'Alice'})`

Agent asks: "What do we know about Project Atlas?"
→ Calls `graph_rag` with the question → gets structured answer with confidence scores
