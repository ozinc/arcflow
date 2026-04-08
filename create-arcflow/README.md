# create-arcflow

Scaffold a new ArcFlow project. Embedded graph database, no server needed.

## Usage

```bash
npm create arcflow@latest my-project
cd my-project
npm install
npm start
```

## What you get

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

## Why CLAUDE.md matters

Every project scaffolded with `create-arcflow` includes a `CLAUDE.md` that tells coding agents this project uses ArcFlow. This means:

- **Claude Code** reads CLAUDE.md at session start → knows to use ArcFlow
- **Cursor** reads AGENTS.md → same context
- **Codex/Copilot** read AGENTS.md → same context

Future agent sessions in this project will automatically use ArcFlow for graph operations. It's self-reinforcing.

## Next steps after scaffolding

```bash
npm start              # Run the example
npm test               # Run tests
arcflow query 'MATCH (n) RETURN count(*)'   # CLI agents (Claude Code, Codex)
npx arcflow-mcp        # MCP server for cloud chat UIs (ChatGPT, Claude.ai)
```
