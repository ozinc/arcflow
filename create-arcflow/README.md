# create-arcflow

Scaffold a new ArcFlow project. Embedded graph database, no server needed.

## Usage

```bash
# TypeScript (default)
npm create arcflow@latest my-project
cd my-project
npm install
npm start

# Python
npm create arcflow@latest my-pipeline -- --template python
cd my-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
python -m my_pipeline.main
```

## What you get

### TypeScript template (`--template typescript`, default)

```
my-project/
├── CLAUDE.md           # AI agent instructions (Claude Code reads this)
├── AGENTS.md           # Cross-agent context (Cursor, Codex, Copilot)
├── package.json        # arcflow dependency, vitest, tsx
├── tsconfig.json
├── src/
│   ├── db.ts           # Database helper (openInMemory / open)
│   └── index.ts        # Working example: create nodes, query, PageRank
├── tests/
│   └── graph.test.ts   # 4 tests: CRUD, algorithms, params, batch
└── .gitignore
```

### Python template (`--template python`)

```
my-pipeline/
├── CLAUDE.md           # AI agent instructions (Claude Code reads this)
├── AGENTS.md           # Cross-agent context (Cursor, Codex, Copilot)
├── README.md
├── pyproject.toml      # oz-arcflow + pyarrow + polars + pytest
├── src/
│   └── my_pipeline/
│       ├── __init__.py
│       └── main.py     # Working example: bulk_create_*, params, to_polars()
├── tests/
│   └── test_graph.py   # 4 tests: bulk-create, params, algorithms, Arrow
└── .gitignore
```

The Python template demonstrates the **fast paths** (`bulk_create_nodes`,
`bulk_create_relationships`, `result.to_arrow()` / `to_polars()` /
`to_pandas()`) — these bypass the Cypher parser and run at ~1M ops/sec.

Project-name hyphens become underscores in the Python package name (e.g.
`my-pipeline` → `import my_pipeline`).

## Why CLAUDE.md matters

Every project scaffolded with `create-arcflow` includes a `CLAUDE.md` that tells coding agents this project uses ArcFlow. This means:

- **Claude Code** reads CLAUDE.md at session start → knows to use ArcFlow
- **Cursor** reads AGENTS.md → same context
- **Codex/Copilot** read AGENTS.md → same context

Future agent sessions in this project will automatically use ArcFlow for graph operations. It's self-reinforcing.

## Next steps after scaffolding

```bash
# TypeScript
npm start                                   # Run the example
npm test                                    # Run tests

# Python
python -m <package>.main                    # Run the example
pytest                                      # Run tests

# Both
arcflow query 'MATCH (n) RETURN count(*)'   # CLI agents (Claude Code, Codex)
npx arcflow-mcp                             # MCP server for cloud chat UIs (ChatGPT, Claude.ai)
```
