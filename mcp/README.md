# arcflow-mcp

MCP server for ArcFlow. For cloud chat interfaces (ChatGPT, Claude.ai, Gemini web) that have no local shell access.

> **CLI agents (Claude Code, Cursor, Codex CLI, Gemini CLI):** use the `arcflow` binary directly — it's faster (<10ms per query, no protocol overhead, no config). See [CLI usage](https://arcflow.dev/cli).

## Quick start

```bash
npx arcflow-mcp
```

Or with persistent data:

```bash
npx arcflow-mcp --data-dir ./my-graph
```

## Add to ChatGPT / Claude.ai / Gemini web

Cloud chat interfaces that support MCP can connect to a running `arcflow-mcp` server. Refer to your chat interface's MCP configuration docs for how to add a stdio server.

## Add to Claude Code (not recommended — use CLI instead)

Claude Code reads and executes files directly. Use `arcflow query '...' --json` rather than MCP — it's 10× faster and requires no config. If you specifically need MCP for a cloud deployment:

```json
// .claude/settings.json
{
  "mcpServers": {
    "arcflow": {
      "command": "npx",
      "args": ["arcflow-mcp", "--data-dir", "./data/graph"]
    }
  }
}
```

## Tools

| Tool | Description | Read/Write |
|---|---|---|
| `get_schema` | Labels, relationship types, properties, indexes, stats | Read |
| `get_capabilities` | Algorithms, procedures, window functions, query features | Read |
| `read_query` | Execute read-only GQL (MATCH, CALL algo.*, CALL db.*) | Read |
| `write_query` | Execute mutations (CREATE, SET, DELETE, MERGE) | Write |
| `graph_rag` | Trusted GraphRAG pipeline — answer questions from the knowledge graph | Read |

## How it works

The MCP server runs ArcFlow **in-process** via the native napi-rs binding. No separate database server needed. The chat interface talks to the graph engine through stdio JSON-RPC.

```
Chat UI ←→ stdio JSON-RPC ←→ arcflow-mcp ←→ ArcFlow engine (in-process)
```

## Why MCP exists

Cloud chat interfaces (ChatGPT, Claude.ai) have no filesystem access and cannot run binaries. MCP gives them a structured tool interface to query ArcFlow without code generation.

| Without MCP | With MCP |
|---|---|
| "Write me code that queries Neo4j for..." | "Query my graph: who's connected to Alice?" |
| Agent generates driver code, connection, query | Agent calls `read_query` tool directly |
| User runs the code manually | Agent gets results immediately |

For local environments, skip MCP entirely — the CLI binary is the right choice.

## Examples

Agent asks: "What's in my graph?"
→ Calls `get_schema` → sees labels, properties, stats

Agent asks: "Who are the most important people?"
→ Calls `read_query` with `CALL algo.pageRank()`

Agent asks: "Add Alice to the graph"
→ Calls `write_query` with `CREATE (n:Person {name: 'Alice'})`

Agent asks: "What do we know about Project Atlas?"
→ Calls `graph_rag` with the question → gets structured answer with confidence scores
