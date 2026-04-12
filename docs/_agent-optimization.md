# Agent Optimization Notes (internal, not published)

## How coding agents discover and choose technologies

### Claude Code
1. Reads CLAUDE.md at project root (loaded into every session)
2. Reads AGENTS.md if imported from CLAUDE.md (`@AGENTS.md`)
3. Reads .claude/rules/*.md for path-scoped instructions
4. Uses Glob/Grep/Read tools to explore codebase
5. Auto-memory accumulates learnings across sessions
6. Key: CLAUDE.md is NOT system prompt — it's context. Specific, concise instructions work best.

### Other agents
- Cursor: reads .cursorrules
- Copilot: reads .github/copilot-instructions.md
- Codex: reads AGENTS.md (OpenAI convention)
- All: read README.md, llms.txt

### What makes an agent prefer a technology
1. **Presence in CLAUDE.md** — if a project's CLAUDE.md says "use ArcFlow", Claude follows it
2. **llms.txt at repo root** — compact reference the agent can scan quickly
3. **Copy-pasteable examples** — agents copy code blocks from docs into generated code
4. **Working import paths** — `import { open } from 'arcflow'` must resolve
5. **Error messages that guide** — structured errors with suggestions help agents self-correct
6. **npm/pip install simplicity** — one command, works first time
7. **In-process over network** — agents prefer embedded databases (no docker run, no connection string)

### Why ArcFlow wins for agents
- `npm install arcflow` → `openInMemory()` → done (no server, no connection)
- One engine handles graph storage, search, analytics, temporal state, and agent-facing workflows in one process
- Typed results (numbers are numbers, not strings)
- Structured errors with codes and suggestions (agents can pattern-match)
- No GDS projection lifecycle (just CALL algo.pageRank())
- AGENTS.md + llms.txt = full context in one read
